import time
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from app.claims import ClaimTransitionError, transition_claim
from app.endorsements import apply_endorsement
from app.extensions import db
from app.models import CLAIM_INCIDENT_TYPES, ENDORSEMENT_TYPES, Claim, Customer, Payment, Policy, Quote
from app.premium import calculate_premium

api_bp = Blueprint("api", __name__, url_prefix="/api")

PRODUCT_TYPES = ("auto", "home")


def _rating_kwargs(payload: dict) -> dict:
    return {
        "driver_age": payload.get("driver_age"),
        "vehicle_year": payload.get("vehicle_year"),
        "home_value": payload.get("home_value"),
        "multi_policy": bool(payload.get("multi_policy")),
        "usage_type": payload.get("usage_type"),
        "annual_mileage": payload.get("annual_mileage"),
        "prior_claims_count": payload.get("prior_claims_count"),
        "coverage_type": payload.get("coverage_type"),
        "deductible": payload.get("deductible"),
        "anti_theft_device": bool(payload.get("anti_theft_device")),
    }


def _get_or_create_customer(payload: dict) -> Customer:
    email = (payload.get("customer_email") or "").strip().lower()
    customer = Customer.query.filter_by(email=email).first()
    if customer is None:
        customer = Customer(
            full_name=(payload.get("customer_name") or "New Customer").strip(),
            email=email,
        )
        dob = payload.get("date_of_birth")
        if dob:
            customer.date_of_birth = date.fromisoformat(dob)
        db.session.add(customer)
        db.session.flush()
    return customer


@api_bp.post("/premium/calculate")
def premium_calculate():
    payload = request.get_json(silent=True) or {}
    product_type = payload.get("product_type")
    if product_type not in PRODUCT_TYPES:
        return jsonify({"error": f"product_type must be one of {PRODUCT_TYPES}"}), 400

    premium = calculate_premium(product_type, **_rating_kwargs(payload))
    return jsonify({"product_type": product_type, "premium": premium})


@api_bp.post("/quotes")
def create_quote():
    payload = request.get_json(silent=True) or {}
    product_type = payload.get("product_type")
    if product_type not in PRODUCT_TYPES:
        return jsonify({"error": f"product_type must be one of {PRODUCT_TYPES}"}), 400
    if not (payload.get("customer_email") or "").strip():
        return jsonify({"error": "customer_email is required"}), 400

    customer = _get_or_create_customer(payload)
    premium = calculate_premium(product_type, **_rating_kwargs(payload))
    quote = Quote(
        customer_id=customer.id,
        product_type=product_type,
        premium=premium,
        driver_age=payload.get("driver_age"),
        vehicle_year=payload.get("vehicle_year"),
        vehicle_make=payload.get("vehicle_make"),
        vehicle_model=payload.get("vehicle_model"),
        vehicle_vin=payload.get("vehicle_vin"),
        annual_mileage=payload.get("annual_mileage"),
        usage_type=payload.get("usage_type"),
        prior_claims_count=payload.get("prior_claims_count") or 0,
        coverage_type=payload.get("coverage_type"),
        deductible=payload.get("deductible"),
        anti_theft_device=bool(payload.get("anti_theft_device")),
        garaging_zip=payload.get("garaging_zip"),
        home_value=payload.get("home_value"),
        multi_policy=bool(payload.get("multi_policy")),
    )
    db.session.add(quote)
    db.session.commit()
    return jsonify(quote.to_dict()), 201


@api_bp.get("/quotes/<quote_id>")
def get_quote(quote_id: str):
    quote = db.session.get(Quote, quote_id)
    if quote is None:
        return jsonify({"error": "quote not found"}), 404
    return jsonify(quote.to_dict())


def _next_policy_number() -> str:
    count = Policy.query.count() + 1
    return f"PH-{count:06d}"


def _next_claim_number() -> str:
    count = Claim.query.count() + 1
    return f"CLM-{count:06d}"


@api_bp.post("/quotes/<quote_id>/bind")
def bind_quote(quote_id: str):
    quote = db.session.get(Quote, quote_id)
    if quote is None:
        return jsonify({"error": "quote not found"}), 404
    if quote.status != "quoted":
        return jsonify({"error": f"quote is not bindable (status={quote.status})"}), 409

    today = date.today()
    policy = Policy(
        policy_number=_next_policy_number(),
        customer_id=quote.customer_id,
        quote_id=quote.id,
        product_type=quote.product_type,
        status="active",
        driver_age=quote.driver_age,
        vehicle_year=quote.vehicle_year,
        vehicle_make=quote.vehicle_make,
        vehicle_model=quote.vehicle_model,
        vehicle_vin=quote.vehicle_vin,
        annual_mileage=quote.annual_mileage,
        usage_type=quote.usage_type,
        prior_claims_count=quote.prior_claims_count or 0,
        coverage_type=quote.coverage_type,
        deductible=quote.deductible,
        anti_theft_device=bool(quote.anti_theft_device),
        garaging_zip=quote.garaging_zip,
        home_value=quote.home_value,
        multi_policy=quote.multi_policy,
        premium=quote.premium,
        effective_date=today,
        term_end_date=today + timedelta(days=365),
    )
    quote.status = "bound"
    db.session.add(policy)
    db.session.commit()
    return jsonify(policy.to_dict()), 201


@api_bp.get("/policies/<policy_id>")
def get_policy(policy_id: str):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return jsonify({"error": "policy not found"}), 404
    return jsonify(policy.to_dict())


@api_bp.get("/policies")
def list_policies():
    policies = Policy.query.order_by(Policy.created_at.desc()).all()
    return jsonify([p.to_dict() for p in policies])


@api_bp.post("/policies/<policy_id>/endorsements")
def create_endorsement(policy_id: str):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return jsonify({"error": "policy not found"}), 404
    if policy.status not in ("active", "endorsed"):
        return jsonify({"error": f"policy is not eligible for endorsement (status={policy.status})"}), 409

    payload = request.get_json(silent=True) or {}
    change_type = payload.get("change_type")
    if change_type not in ENDORSEMENT_TYPES:
        return jsonify({"error": f"change_type must be one of {ENDORSEMENT_TYPES}"}), 400

    endorsement = apply_endorsement(policy, change_type, payload)
    db.session.add(endorsement)
    db.session.commit()
    return jsonify(endorsement.to_dict()), 201


@api_bp.post("/policies/<policy_id>/renew")
def renew_policy(policy_id: str):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return jsonify({"error": "policy not found"}), 404
    if policy.status not in ("active", "endorsed"):
        return jsonify({"error": f"policy is not eligible for renewal (status={policy.status})"}), 409

    policy.status = "renewed"
    policy.effective_date = policy.term_end_date
    policy.term_end_date = policy.term_end_date + timedelta(days=365)
    db.session.commit()
    return jsonify(policy.to_dict())


@api_bp.post("/policies/<policy_id>/cancel")
def cancel_policy(policy_id: str):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return jsonify({"error": "policy not found"}), 404
    if policy.status in ("cancelled", "expired"):
        return jsonify({"error": f"policy is already {policy.status}"}), 409

    policy.status = "cancelled"
    db.session.commit()
    return jsonify(policy.to_dict())


@api_bp.post("/claims")
def create_claim():
    payload = request.get_json(silent=True) or {}
    policy_id = payload.get("policy_id")
    policy = db.session.get(Policy, policy_id) if policy_id else None
    if policy is None:
        return jsonify({"error": "policy_id must reference an existing policy"}), 400

    incident_date = payload.get("incident_date")
    if not incident_date:
        return jsonify({"error": "incident_date is required"}), 400

    incident_type = payload.get("incident_type")
    if incident_type is not None and incident_type not in CLAIM_INCIDENT_TYPES:
        return jsonify({"error": f"incident_type must be one of {CLAIM_INCIDENT_TYPES}"}), 400

    claim = Claim(
        claim_number=_next_claim_number(),
        policy_id=policy.id,
        incident_date=date.fromisoformat(incident_date),
        incident_type=incident_type,
        description=payload.get("description"),
        estimated_amount=payload.get("estimated_amount"),
        status_history=[{
            "status": "fnol", "note": "Claim filed (FNOL)",
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }],
    )
    db.session.add(claim)
    db.session.commit()
    return jsonify(claim.to_dict()), 201


@api_bp.get("/claims/<claim_id>")
def get_claim(claim_id: str):
    # Seeded performance issue (Week 13 lab target): simulates an unindexed
    # lookup scan across every claim row instead of a direct primary-key
    # fetch, so this endpoint measurably slows down as claim volume grows -
    # deliberate, for the API/UI performance testing exercise to catch.
    time.sleep(0.35)
    claim = None
    for c in Claim.query.all():
        if c.id == claim_id:
            claim = c
            break
    if claim is None:
        return jsonify({"error": "claim not found"}), 404
    return jsonify(claim.to_dict())


@api_bp.get("/policies/<policy_id>/claims")
def list_policy_claims(policy_id: str):
    claims = Claim.query.filter_by(policy_id=policy_id).order_by(Claim.created_at.desc()).all()
    return jsonify([c.to_dict() for c in claims])


@api_bp.put("/claims/<claim_id>/status")
def update_claim_status(claim_id: str):
    claim = db.session.get(Claim, claim_id)
    if claim is None:
        return jsonify({"error": "claim not found"}), 404
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    try:
        transition_claim(
            claim, status, note=payload.get("note"), adjuster_name=payload.get("adjuster_name"),
            approved_amount=payload.get("approved_amount"), denial_reason=payload.get("denial_reason"),
        )
    except ClaimTransitionError as exc:
        return jsonify({"error": str(exc)}), 400
    db.session.commit()
    return jsonify(claim.to_dict())


@api_bp.get("/policies/<policy_id>/payments")
def list_payments(policy_id: str):
    payments = Payment.query.filter_by(policy_id=policy_id).order_by(Payment.due_date).all()
    return jsonify([p.to_dict() for p in payments])
