"""Shared Mid-Term Adjustment (MTA) / endorsement logic, used by both the
JSON API (routes_api.py) and the web CSR workspace (routes_web.py) so a
policy change behaves identically - and recalculates premium the same way -
regardless of which surface a learner is practicing against."""
from app.models import FIELD_DRIVEN_ENDORSEMENT_TYPES, Endorsement, Policy
from app.premium import calculate_premium

# Which policy fields each field-driven endorsement type may change.
ENDORSEMENT_FIELD_MAP = {
    "coverage_change": ("coverage_type", "deductible"),
    "vehicle_update": ("vehicle_make", "vehicle_model", "vehicle_year", "vehicle_vin"),
    "usage_update": ("usage_type", "annual_mileage", "anti_theft_device"),
}


def apply_endorsement(policy: Policy, change_type: str, payload: dict) -> Endorsement:
    """For a field-driven change_type, applies the submitted new values to
    the policy, records old->new per field, and recomputes the premium
    delta by re-running calculate_premium() rather than trusting a
    manually-typed number - a real MTA, not just a logged note. For the two
    non-field-backed types (no address/multi-driver data model exists yet),
    falls back to a manually-entered delta, same as the original behavior."""
    field_changes = None
    if change_type in FIELD_DRIVEN_ENDORSEMENT_TYPES:
        field_changes = {}
        for field in ENDORSEMENT_FIELD_MAP[change_type]:
            if field not in payload or payload[field] in (None, ""):
                continue
            old_value = getattr(policy, field)
            new_value = payload[field]
            if field == "anti_theft_device":
                new_value = bool(new_value) if not isinstance(new_value, bool) else new_value
            elif field in ("vehicle_year", "annual_mileage", "deductible"):
                new_value = int(new_value)
            if new_value != old_value:
                field_changes[field] = {"old": old_value, "new": new_value}
                setattr(policy, field, new_value)

        old_premium = policy.premium
        new_premium = calculate_premium(
            policy.product_type, driver_age=policy.driver_age, vehicle_year=policy.vehicle_year,
            home_value=policy.home_value, multi_policy=policy.multi_policy, usage_type=policy.usage_type,
            annual_mileage=policy.annual_mileage, prior_claims_count=policy.prior_claims_count,
            coverage_type=policy.coverage_type, deductible=policy.deductible,
            anti_theft_device=policy.anti_theft_device,
        )
        premium_delta = round(new_premium - old_premium, 2)
        policy.premium = new_premium
    else:
        premium_delta = float(payload.get("premium_delta") or 0)
        policy.premium = round(policy.premium + premium_delta, 2)

    endorsement = Endorsement(
        policy_id=policy.id, change_type=change_type, description=payload.get("description"),
        field_changes=field_changes, premium_delta=premium_delta,
    )
    policy.status = "endorsed"
    return endorsement
