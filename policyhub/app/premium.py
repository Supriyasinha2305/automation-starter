"""Premium calculation for PolicyHub quotes. Intentionally includes one
seeded boundary bug (see the age == 25 comment below) so Week 4's
boundary-value-analysis exercise has a real, findable defect - it is
deliberate, not an oversight."""
from datetime import date

CURRENT_YEAR = date.today().year


def calculate_premium(
    product_type, driver_age=None, vehicle_year=None, home_value=None, multi_policy=False,
    usage_type=None, annual_mileage=None, prior_claims_count=None, coverage_type=None,
    deductible=None, anti_theft_device=False,
):
    """Auto rating factors beyond age/year are additive on top of the
    original base+age+year calculation below (left untouched, including the
    seeded age==25 boundary bug) so every pre-existing quote/test that only
    passes driver_age/vehicle_year still gets exactly the same premium as
    before - the new factors only kick in when a caller actually supplies
    them, matching how a real insurer layers rating factors."""
    if product_type == "auto":
        base = 800.0
        if driver_age is not None:
            if driver_age < 18:
                base += 600
            elif driver_age < 21:
                base += 350
            elif driver_age < 25:
                base += 150
            elif driver_age > 25:
                # Seeded boundary bug: the "mature driver" discount should
                # apply at age >= 25, but this checks > 25, so a driver who
                # is exactly 25 falls through with no adjustment at all -
                # the exact boundary a BVA test case should catch.
                base -= 100
        if vehicle_year is not None:
            vehicle_age = CURRENT_YEAR - vehicle_year
            if vehicle_age > 15:
                base += 100

        # Usage - commercial/rideshare use carries materially higher risk.
        if usage_type == "commercial":
            base += 300
        elif usage_type == "rideshare":
            base += 250

        # Annual mileage - higher exposure at high mileage, small discount
        # for genuinely low usage.
        if annual_mileage is not None:
            if annual_mileage > 15000:
                base += 150
            elif annual_mileage < 5000:
                base -= 50

        # Claims history - each prior claim raises risk; capped at 3 so one
        # very claim-heavy driver doesn't dominate the whole calculation.
        if prior_claims_count:
            base += min(prior_claims_count, 3) * 120

        # Coverage level - broader coverage costs more to underwrite.
        if coverage_type == "collision":
            base += 200
        elif coverage_type == "comprehensive":
            base += 350

        # Deductible - the classic inverse relationship: a lower deductible
        # (insurer takes on more of each claim) raises premium; a higher
        # deductible lowers it. 1000 is treated as the neutral baseline.
        if deductible is not None:
            if deductible <= 250:
                base += 150
            elif deductible <= 500:
                base += 75
            elif deductible >= 2500:
                base -= 100

        # Anti-theft device - a standard small safety/security discount.
        if anti_theft_device:
            base -= 40
    else:
        base = 500.0
        if home_value:
            base += home_value * 0.002

    if multi_policy:
        base *= 0.9

    return round(base, 2)
