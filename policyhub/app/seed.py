"""Demo data for PolicyHub. Seeds the three named "hero" customers referenced
throughout the SQValex training curriculum EXACTLY as before (Sam Rivera's
age==25 boundary-bug policy, Priya Nandan's multi-policy-discount home
policy, Jordan Blake's near-renewal auto policy with a claim) as PH-000001
through PH-000003, then generates 42 additional realistic customers/policies
(mostly auto, per the training program's explicit ask for richer auto
coverage) so students have a real ~45-row dataset to query, reconcile, and
practice against - in SQL (ETL Testing), API testing, accessibility scans,
performance tests, and everywhere else PolicyHub is the practice target.

Deterministic (fixed random seed) so every fresh instance gets the same
dataset shape, making training exercises and their expected answers
reproducible across students."""
import random
from datetime import date, timedelta

from app.extensions import db
from app.models import Claim, Customer, Payment, Policy
from app.premium import calculate_premium

FIRST_NAMES = (
    "Alex", "Morgan", "Taylor", "Jordan", "Casey", "Riley", "Jamie", "Avery",
    "Parker", "Quinn", "Reese", "Rowan", "Skyler", "Drew", "Emerson", "Hayden",
    "Kendall", "Logan", "Marlowe", "Peyton", "Sawyer", "Shawn", "Blair", "Cameron",
    "Devon", "Elliot", "Finley", "Gray", "Harper", "Indigo", "Jules", "Kai",
    "Lane", "Micah", "Noel", "Ocean", "Presley", "Remy", "Sage", "Tatum",
    "Val", "Wren", "Yael", "Zion",
)
LAST_NAMES = (
    "Nguyen", "Garcia", "Smith", "Patel", "Kim", "Johnson", "Martinez", "Chen",
    "Okafor", "Rossi", "Muller", "Dubois", "Ivanov", "Silva", "Kowalski", "Haddad",
    "Andersen", "Fischer", "Tanaka", "Santos", "Novak", "Petrova", "Alvarez", "Schmidt",
    "Costa", "Larsen", "Reyes", "Hoffmann", "Baptiste", "Moreau", "Weber", "Sato",
    "Diallo", "Kaur", "Lindqvist", "Brennan", "Torres", "Vogel", "Ahn", "Bianchi",
    "Carter", "Dahl", "Esposito", "Falk",
)
VEHICLES = (
    ("Toyota", "Camry"), ("Honda", "Civic"), ("Ford", "F-150"), ("Tesla", "Model 3"),
    ("Chevrolet", "Silverado"), ("Nissan", "Altima"), ("Jeep", "Wrangler"), ("Subaru", "Outback"),
    ("BMW", "3 Series"), ("Hyundai", "Elantra"), ("Kia", "Soul"), ("Mazda", "CX-5"),
    ("Ram", "1500"), ("Volkswagen", "Jetta"), ("Audi", "A4"), ("Honda", "CR-V"),
    ("Toyota", "RAV4"), ("Ford", "Escape"), ("Chevrolet", "Equinox"), ("Subaru", "Impreza"),
)
ZIP_CODES = ("60601", "94103", "10001", "30301", "75201", "98101", "02108", "80202", "33101", "85001")
INCIDENT_TYPES = ("collision", "theft", "weather", "liability", "fire", "vandalism", "other")
ADJUSTERS = ("Jordan Blake", "Priya Nandan", "Morgan Reyes", "Avery Kim")

# Pre-scripted claim histories per target end-status, walking only valid
# CLAIM_TRANSITIONS moves - so every seeded claim's status_history is a
# genuine, reproducible FNOL-through-closure (or denial/reopen) path, not
# just a status flipped with no trail behind it.
CLAIM_PATHS = {
    "fnol": ("fnol",),
    "under_review": ("fnol", "under_review"),
    "approved": ("fnol", "under_review", "approved"),
    "denied": ("fnol", "under_review", "denied"),
    "closed": ("fnol", "under_review", "approved", "closed"),
    "reopened": ("fnol", "under_review", "denied", "reopened"),
}


def _unique_customers(n: int, rng: random.Random) -> list[tuple[str, str]]:
    """Returns n distinct (full_name, email) pairs."""
    seen_emails = set()
    people = []
    while len(people) < n:
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}@example.com"
        if email in seen_emails:
            continue
        seen_emails.add(email)
        people.append((f"{first} {last}", email))
    return people


def _weighted(rng: random.Random, choices: dict):
    items = list(choices.items())
    return rng.choices([v for v, _ in items], weights=[w for _, w in items], k=1)[0]


def _build_claim(policy: Policy, claim_no: int, today: date, rng: random.Random) -> Claim:
    target_status = _weighted(rng, {
        "closed": 40, "approved": 15, "under_review": 15, "denied": 10, "fnol": 15, "reopened": 5,
    })
    path = CLAIM_PATHS[target_status]
    incident_date = today - timedelta(days=rng.randint(5, 250))

    history = []
    step_date = incident_date
    for i, status in enumerate(path):
        note = {
            "fnol": "Claim filed (FNOL)",
            "under_review": "Adjuster assigned, reviewing evidence",
            "approved": "Claim approved for payout",
            "denied": "Claim denied - see denial reason",
            "closed": "Claim closed",
            "reopened": "Reopened for further review",
        }[status]
        history.append({"status": status, "note": note, "changed_at": step_date.isoformat() + "T00:00:00+00:00"})
        step_date = step_date + timedelta(days=rng.randint(1, 5))

    estimated = round(rng.uniform(400, 12000), 2)
    claim = Claim(
        claim_number=f"CLM-{claim_no:06d}", policy_id=policy.id, incident_date=incident_date,
        incident_type=rng.choice(INCIDENT_TYPES), description=None, status=target_status,
        estimated_amount=estimated, status_history=history,
    )
    if target_status in ("approved", "closed"):
        claim.approved_amount = round(estimated * rng.uniform(0.7, 1.0), 2)
        claim.adjuster_name = rng.choice(ADJUSTERS)
    if target_status in ("denied", "reopened"):
        claim.denial_reason = rng.choice((
            "Loss not covered under current policy terms.",
            "Incident occurred outside the policy's effective period.",
            "Insufficient documentation provided to substantiate the claim.",
        ))
        claim.adjuster_name = rng.choice(ADJUSTERS)
    if target_status == "under_review":
        claim.adjuster_name = rng.choice(ADJUSTERS)
    return claim


def seed_demo_data() -> None:
    if Customer.query.count() > 0:
        return

    today = date.today()
    rng = random.Random(20240101)  # fixed seed: same dataset shape every fresh instance

    sam = Customer(full_name="Sam Rivera", email="sam.rivera@example.com", date_of_birth=date(1994, 6, 12))
    priya_customer = Customer(full_name="Priya Nandan", email="priya.nandan@example.com", date_of_birth=date(1988, 3, 2))
    jordan_customer = Customer(full_name="Jordan Blake", email="jordan.blake@example.com", date_of_birth=date(1979, 11, 20))
    db.session.add_all([sam, priya_customer, jordan_customer])
    db.session.flush()

    # Sam: auto policy, driver age exactly 25 - lands on the seeded boundary bug
    sam_premium = calculate_premium("auto", driver_age=25, vehicle_year=2019, multi_policy=False)
    sam_policy = Policy(
        policy_number="PH-000001", customer_id=sam.id, product_type="auto", status="active",
        driver_age=25, vehicle_year=2019, vehicle_make="Honda", vehicle_model="Civic",
        usage_type="personal", annual_mileage=11000, prior_claims_count=0,
        coverage_type="collision", deductible=1000, anti_theft_device=False, garaging_zip="60601",
        multi_policy=False, premium=sam_premium,
        effective_date=today - timedelta(days=60), term_end_date=today + timedelta(days=305),
    )

    # Priya: home policy, multi-policy discount
    priya_premium = calculate_premium("home", home_value=350000, multi_policy=True)
    priya_policy = Policy(
        policy_number="PH-000002", customer_id=priya_customer.id, product_type="home", status="active",
        home_value=350000, multi_policy=True, premium=priya_premium,
        effective_date=today - timedelta(days=200), term_end_date=today + timedelta(days=165),
    )

    # Jordan: auto policy nearing renewal, with a claim under review
    jordan_premium = calculate_premium("auto", driver_age=46, vehicle_year=2011, multi_policy=False)
    jordan_policy = Policy(
        policy_number="PH-000003", customer_id=jordan_customer.id, product_type="auto", status="active",
        driver_age=46, vehicle_year=2011, vehicle_make="Subaru", vehicle_model="Outback",
        usage_type="personal", annual_mileage=9500, prior_claims_count=1,
        coverage_type="comprehensive", deductible=500, anti_theft_device=True, garaging_zip="02108",
        multi_policy=False, premium=jordan_premium,
        effective_date=today - timedelta(days=350), term_end_date=today + timedelta(days=15),
    )

    db.session.add_all([sam_policy, priya_policy, jordan_policy])
    db.session.flush()

    claim = Claim(
        claim_number="CLM-000001", policy_id=jordan_policy.id,
        incident_date=today - timedelta(days=10), incident_type="collision",
        description="Rear-end collision in parking lot, minor bumper damage.",
        status="under_review", estimated_amount=1850.0, adjuster_name="Priya Nandan",
        status_history=[
            {"status": "fnol", "note": "Claim filed (FNOL)", "changed_at": (today - timedelta(days=10)).isoformat() + "T00:00:00+00:00"},
            {"status": "under_review", "note": "Adjuster assigned, reviewing evidence", "changed_at": (today - timedelta(days=8)).isoformat() + "T00:00:00+00:00"},
        ],
    )
    db.session.add(claim)

    hero_policies = [sam_policy, priya_policy, jordan_policy]
    for policy in hero_policies:
        db.session.add(Payment(policy_id=policy.id, amount=round(policy.premium / 12, 2), due_date=today + timedelta(days=5), status="due"))
        db.session.add(Payment(policy_id=policy.id, amount=round(policy.premium / 12, 2), due_date=today - timedelta(days=25), paid_at=today - timedelta(days=25), status="paid"))

    # --- 42 additional customers/policies, ~78% auto / ~22% home -----------
    people = _unique_customers(42, rng)
    all_policies = list(hero_policies)
    policy_seq = 4
    claim_seq = 2

    for full_name, email in people:
        dob_year = today.year - rng.randint(18, 75)
        customer = Customer(full_name=full_name, email=email, date_of_birth=date(dob_year, rng.randint(1, 12), rng.randint(1, 28)))
        db.session.add(customer)
        db.session.flush()

        product_type = _weighted(rng, {"auto": 78, "home": 22})
        multi_policy = rng.random() < 0.25
        status = _weighted(rng, {"active": 65, "renewed": 10, "cancelled": 8, "lapsed": 7, "expired": 5, "endorsed": 5})

        days_ago = rng.randint(10, 400)
        effective_date = today - timedelta(days=days_ago)
        term_end_date = effective_date + timedelta(days=365)
        if status == "expired":
            term_end_date = today - timedelta(days=rng.randint(1, 60))

        kwargs = dict(
            policy_number=f"PH-{policy_seq:06d}", customer_id=customer.id, product_type=product_type,
            status=status, multi_policy=multi_policy,
            effective_date=effective_date, term_end_date=term_end_date,
        )

        if product_type == "auto":
            make, model = rng.choice(VEHICLES)
            # A few driver ages deliberately land on classic BVA boundaries
            # (18, 21, 25) in addition to the broader random spread.
            driver_age = rng.choice((18, 21, 25)) if rng.random() < 0.15 else rng.randint(17, 80)
            vehicle_year = rng.randint(1998, 2026)
            usage_type = _weighted(rng, {"personal": 70, "commercial": 20, "rideshare": 10})
            annual_mileage = rng.choice((rng.randint(1000, 4999), rng.randint(15001, 30000), rng.randint(5000, 15000)))
            prior_claims_count = _weighted(rng, {0: 60, 1: 20, 2: 10, 3: 7, 4: 3})
            coverage_type = _weighted(rng, {"liability_only": 35, "collision": 35, "comprehensive": 30})
            deductible = rng.choice((250, 500, 1000, 2500))
            anti_theft_device = rng.random() < 0.35
            garaging_zip = rng.choice(ZIP_CODES)

            premium = calculate_premium(
                "auto", driver_age=driver_age, vehicle_year=vehicle_year, multi_policy=multi_policy,
                usage_type=usage_type, annual_mileage=annual_mileage, prior_claims_count=prior_claims_count,
                coverage_type=coverage_type, deductible=deductible, anti_theft_device=anti_theft_device,
            )
            kwargs.update(
                driver_age=driver_age, vehicle_year=vehicle_year, vehicle_make=make, vehicle_model=model,
                annual_mileage=annual_mileage, usage_type=usage_type, prior_claims_count=prior_claims_count,
                coverage_type=coverage_type, deductible=deductible, anti_theft_device=anti_theft_device,
                garaging_zip=garaging_zip, premium=premium,
            )
        else:
            home_value = round(rng.uniform(150000, 750000), -3)
            premium = calculate_premium("home", home_value=home_value, multi_policy=multi_policy)
            kwargs.update(home_value=home_value, premium=premium)

        policy = Policy(**kwargs)
        db.session.add(policy)
        db.session.flush()
        all_policies.append(policy)
        policy_seq += 1

        # ~30% of auto policies (where a claim makes sense) get 1 claim
        if product_type == "auto" and rng.random() < 0.3:
            claim = _build_claim(policy, claim_seq, today, rng)
            db.session.add(claim)
            claim_seq += 1

        # Payments: mirrors the original pattern (1 due, 1 paid), with a
        # small chance of a missed payment for realistic billing-data variety.
        monthly = round(policy.premium / 12, 2)
        if rng.random() < 0.1:
            db.session.add(Payment(policy_id=policy.id, amount=monthly, due_date=today - timedelta(days=rng.randint(5, 40)), status="missed"))
        else:
            db.session.add(Payment(policy_id=policy.id, amount=monthly, due_date=today + timedelta(days=rng.randint(1, 30)), status="due"))
        db.session.add(Payment(policy_id=policy.id, amount=monthly, due_date=today - timedelta(days=rng.randint(10, 60)), paid_at=today - timedelta(days=rng.randint(10, 60)), status="paid"))

    db.session.commit()
