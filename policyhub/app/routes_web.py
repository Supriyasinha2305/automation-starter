from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, redirect, render_template, request, url_for

from app.claims import ClaimTransitionError, transition_claim
from app.endorsements import apply_endorsement
from app.extensions import db
from app.models import CLAIM_INCIDENT_TYPES, CLAIM_TRANSITIONS, ENDORSEMENT_TYPES, Claim, Customer, Payment, Policy, Quote
from app.premium import calculate_premium

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def home():
    policy_count = Policy.query.count()
    claim_count = Claim.query.count()
    quote_count = Quote.query.count()
    return render_template("home.html", policy_count=policy_count, claim_count=claim_count, quote_count=quote_count)


@web_bp.get("/quote/new")
def quote_new():
    return render_template("quote_new.html")


@web_bp.post("/quote/new")
def quote_create():
    form = request.form
    product_type = form.get("product_type")
    driver_age = form.get("driver_age", type=int)
    vehicle_year = form.get("vehicle_year", type=int)
    vehicle_make = form.get("vehicle_make", "").strip() or None
    vehicle_model = form.get("vehicle_model", "").strip() or None
    vehicle_vin = form.get("vehicle_vin", "").strip() or None
    annual_mileage = form.get("annual_mileage", type=int)
    usage_type = form.get("usage_type") or None
    prior_claims_count = form.get("prior_claims_count", type=int) or 0
    coverage_type = form.get("coverage_type") or None
    deductible = form.get("deductible", type=int)
    anti_theft_device = form.get("anti_theft_device") == "on"
    garaging_zip = form.get("garaging_zip", "").strip() or None
    home_value = form.get("home_value", type=float)
    multi_policy = form.get("multi_policy") == "on"

    customer = Customer.query.filter_by(email=form.get("customer_email", "").strip().lower()).first()
    if customer is None:
        customer = Customer(full_name=form.get("customer_name", "").strip(), email=form.get("customer_email", "").strip().lower())
        db.session.add(customer)
        db.session.flush()

    premium = calculate_premium(
        product_type, driver_age=driver_age, vehicle_year=vehicle_year, home_value=home_value,
        multi_policy=multi_policy, usage_type=usage_type, annual_mileage=annual_mileage,
        prior_claims_count=prior_claims_count, coverage_type=coverage_type, deductible=deductible,
        anti_theft_device=anti_theft_device,
    )
    quote = Quote(
        customer_id=customer.id, product_type=product_type, driver_age=driver_age, vehicle_year=vehicle_year,
        vehicle_make=vehicle_make, vehicle_model=vehicle_model, vehicle_vin=vehicle_vin,
        annual_mileage=annual_mileage, usage_type=usage_type, prior_claims_count=prior_claims_count,
        coverage_type=coverage_type, deductible=deductible, anti_theft_device=anti_theft_device,
        garaging_zip=garaging_zip, home_value=home_value, multi_policy=multi_policy, premium=premium,
    )
    db.session.add(quote)
    db.session.commit()
    return redirect(url_for("web.quote_detail", quote_id=quote.id))


@web_bp.get("/quote/<quote_id>")
def quote_detail(quote_id):
    quote = db.session.get(Quote, quote_id)
    if quote is None:
        return render_template("not_found.html", message="Quote not found"), 404
    return render_template("quote_detail.html", quote=quote)


@web_bp.post("/quote/<quote_id>/bind")
def quote_bind(quote_id):
    quote = db.session.get(Quote, quote_id)
    if quote is None or quote.status != "quoted":
        return render_template("not_found.html", message="Quote not found or already bound"), 404

    today = date.today()
    count = Policy.query.count() + 1
    policy = Policy(
        policy_number=f"PH-{count:06d}", customer_id=quote.customer_id, quote_id=quote.id,
        product_type=quote.product_type, status="active", driver_age=quote.driver_age,
        vehicle_year=quote.vehicle_year, vehicle_make=quote.vehicle_make, vehicle_model=quote.vehicle_model,
        vehicle_vin=quote.vehicle_vin, annual_mileage=quote.annual_mileage, usage_type=quote.usage_type,
        prior_claims_count=quote.prior_claims_count or 0, coverage_type=quote.coverage_type,
        deductible=quote.deductible, anti_theft_device=bool(quote.anti_theft_device),
        garaging_zip=quote.garaging_zip, home_value=quote.home_value, multi_policy=quote.multi_policy,
        premium=quote.premium, effective_date=today, term_end_date=today + timedelta(days=365),
    )
    quote.status = "bound"
    db.session.add(policy)
    db.session.commit()
    return redirect(url_for("web.policy_detail", policy_id=policy.id))


@web_bp.get("/policies")
def policy_queue():
    policies = Policy.query.order_by(Policy.created_at.desc()).all()
    return render_template("policy_queue.html", policies=policies)


@web_bp.get("/policies/<policy_id>")
def policy_detail(policy_id):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return render_template("not_found.html", message="Policy not found"), 404
    return render_template("policy_detail.html", policy=policy)


@web_bp.get("/policies/<policy_id>/endorse")
def endorsement_new(policy_id):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return render_template("not_found.html", message="Policy not found"), 404
    return render_template("endorsement_new.html", policy=policy)


@web_bp.post("/policies/<policy_id>/endorse")
def endorsement_create(policy_id):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return render_template("not_found.html", message="Policy not found"), 404

    form = request.form
    change_type = form.get("change_type")
    if change_type not in ENDORSEMENT_TYPES:
        return render_template("not_found.html", message="Invalid endorsement type"), 400

    payload = {"description": form.get("description"), "premium_delta": form.get("premium_delta", type=float)}
    # Field-driven MTA types submit the new value for each field they cover
    # (pre-filled with the current value in the form, see endorsement_new.html)
    # - convert types explicitly here rather than trusting apply_endorsement's
    # generic coercion, since HTML form values always arrive as strings.
    if change_type == "coverage_change":
        payload["coverage_type"] = form.get("coverage_type") or None
        payload["deductible"] = form.get("deductible", type=int)
    elif change_type == "vehicle_update":
        payload["vehicle_make"] = form.get("vehicle_make", "").strip() or None
        payload["vehicle_model"] = form.get("vehicle_model", "").strip() or None
        payload["vehicle_year"] = form.get("vehicle_year", type=int)
        payload["vehicle_vin"] = form.get("vehicle_vin", "").strip() or None
    elif change_type == "usage_update":
        payload["usage_type"] = form.get("usage_type") or None
        payload["annual_mileage"] = form.get("annual_mileage", type=int)
        payload["anti_theft_device"] = form.get("anti_theft_device") == "yes"

    endorsement = apply_endorsement(policy, change_type, payload)
    db.session.add(endorsement)
    db.session.commit()
    return redirect(url_for("web.policy_detail", policy_id=policy.id))


@web_bp.post("/policies/<policy_id>/renew")
def policy_renew(policy_id):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return render_template("not_found.html", message="Policy not found"), 404
    policy.status = "renewed"
    policy.effective_date = policy.term_end_date
    policy.term_end_date = policy.term_end_date + timedelta(days=365)
    db.session.commit()
    return redirect(url_for("web.policy_detail", policy_id=policy.id))


@web_bp.post("/policies/<policy_id>/cancel")
def policy_cancel(policy_id):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return render_template("not_found.html", message="Policy not found"), 404
    policy.status = "cancelled"
    db.session.commit()
    return redirect(url_for("web.policy_detail", policy_id=policy.id))


@web_bp.get("/policies/<policy_id>/billing")
def billing(policy_id):
    policy = db.session.get(Policy, policy_id)
    if policy is None:
        return render_template("not_found.html", message="Policy not found"), 404
    payments = Payment.query.filter_by(policy_id=policy_id).order_by(Payment.due_date).all()
    return render_template("billing.html", policy=policy, payments=payments)


@web_bp.get("/claims/new")
def claim_new():
    policy_id = request.args.get("policy_id")
    policy = db.session.get(Policy, policy_id) if policy_id else None
    return render_template("claim_new.html", policy=policy, incident_types=CLAIM_INCIDENT_TYPES)


@web_bp.post("/claims/new")
def claim_create():
    form = request.form
    policy = db.session.get(Policy, form.get("policy_id"))
    if policy is None:
        return render_template("not_found.html", message="Policy not found for this claim"), 404

    count = Claim.query.count() + 1
    claim = Claim(
        claim_number=f"CLM-{count:06d}", policy_id=policy.id,
        incident_date=date.fromisoformat(form.get("incident_date")),
        incident_type=form.get("incident_type") or None,
        description=form.get("description"), estimated_amount=form.get("estimated_amount", type=float),
        status_history=[{
            "status": "fnol", "note": "Claim filed (FNOL)",
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }],
    )
    db.session.add(claim)
    db.session.commit()
    return redirect(url_for("web.claim_status", claim_id=claim.id))


@web_bp.get("/claims/<claim_id>")
def claim_status(claim_id):
    claim = db.session.get(Claim, claim_id)
    if claim is None:
        return render_template("not_found.html", message="Claim not found"), 404
    return render_template("claim_status.html", claim=claim, next_statuses=CLAIM_TRANSITIONS.get(claim.status, ()))


@web_bp.post("/claims/<claim_id>/status")
def claim_status_update(claim_id):
    claim = db.session.get(Claim, claim_id)
    if claim is None:
        return render_template("not_found.html", message="Claim not found"), 404

    form = request.form
    try:
        transition_claim(
            claim, form.get("status"), note=form.get("note") or None,
            adjuster_name=form.get("adjuster_name") or None,
            approved_amount=form.get("approved_amount", type=float),
            denial_reason=form.get("denial_reason") or None,
        )
    except ClaimTransitionError as exc:
        return render_template(
            "claim_status.html", claim=claim, error=str(exc),
            next_statuses=CLAIM_TRANSITIONS.get(claim.status, ()),
        )
    db.session.commit()
    return redirect(url_for("web.claim_status", claim_id=claim.id))


@web_bp.get("/portal")
def portal():
    email = (request.args.get("email") or "").strip().lower()
    customer = Customer.query.filter_by(email=email).first() if email else None
    policies = Policy.query.filter_by(customer_id=customer.id).all() if customer else []
    return render_template("portal.html", customer=customer, policies=policies, email=email)
