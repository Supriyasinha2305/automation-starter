import uuid
from datetime import datetime, timezone

from app.extensions import db


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
        }


AUTO_USAGE_TYPES = ("personal", "commercial", "rideshare")
AUTO_COVERAGE_TYPES = ("liability_only", "collision", "comprehensive")
AUTO_DEDUCTIBLES = (250, 500, 1000, 2500)


class Quote(db.Model):
    """A pre-bind quote. Status: quoted -> bound (a Policy is created) | expired."""
    __tablename__ = "quotes"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), nullable=False)
    product_type = db.Column(db.String(10), nullable=False)  # auto | home
    status = db.Column(db.String(20), nullable=False, default="quoted")
    driver_age = db.Column(db.Integer, nullable=True)  # auto only
    vehicle_year = db.Column(db.Integer, nullable=True)  # auto only
    # Auto rating factors (auto only) - added so students can practice on
    # realistic key-vehicle-parameter rating logic, not just age/year.
    vehicle_make = db.Column(db.String(50), nullable=True)
    vehicle_model = db.Column(db.String(50), nullable=True)
    vehicle_vin = db.Column(db.String(17), nullable=True)
    annual_mileage = db.Column(db.Integer, nullable=True)
    usage_type = db.Column(db.String(20), nullable=True)  # personal | commercial | rideshare
    prior_claims_count = db.Column(db.Integer, nullable=True, default=0)
    coverage_type = db.Column(db.String(20), nullable=True)  # liability_only | collision | comprehensive
    deductible = db.Column(db.Integer, nullable=True)
    anti_theft_device = db.Column(db.Boolean, nullable=False, default=False)
    garaging_zip = db.Column(db.String(10), nullable=True)
    home_value = db.Column(db.Float, nullable=True)  # home only
    multi_policy = db.Column(db.Boolean, nullable=False, default=False)
    premium = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    customer = db.relationship("Customer")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.full_name if self.customer else None,
            "product_type": self.product_type,
            "status": self.status,
            "driver_age": self.driver_age,
            "vehicle_year": self.vehicle_year,
            "vehicle_make": self.vehicle_make,
            "vehicle_model": self.vehicle_model,
            "vehicle_vin": self.vehicle_vin,
            "annual_mileage": self.annual_mileage,
            "usage_type": self.usage_type,
            "prior_claims_count": self.prior_claims_count,
            "coverage_type": self.coverage_type,
            "deductible": self.deductible,
            "anti_theft_device": self.anti_theft_device,
            "garaging_zip": self.garaging_zip,
            "home_value": self.home_value,
            "multi_policy": self.multi_policy,
            "premium": self.premium,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


POLICY_STATUSES = ("bound", "active", "endorsed", "renewed", "cancelled", "lapsed", "expired")


class Policy(db.Model):
    __tablename__ = "policies"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    policy_number = db.Column(db.String(32), nullable=False, unique=True)
    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), nullable=False)
    quote_id = db.Column(db.String(36), db.ForeignKey("quotes.id"), nullable=True)
    product_type = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="bound")
    driver_age = db.Column(db.Integer, nullable=True)
    vehicle_year = db.Column(db.Integer, nullable=True)
    vehicle_make = db.Column(db.String(50), nullable=True)
    vehicle_model = db.Column(db.String(50), nullable=True)
    vehicle_vin = db.Column(db.String(17), nullable=True)
    annual_mileage = db.Column(db.Integer, nullable=True)
    usage_type = db.Column(db.String(20), nullable=True)
    prior_claims_count = db.Column(db.Integer, nullable=True, default=0)
    coverage_type = db.Column(db.String(20), nullable=True)
    deductible = db.Column(db.Integer, nullable=True)
    anti_theft_device = db.Column(db.Boolean, nullable=False, default=False)
    garaging_zip = db.Column(db.String(10), nullable=True)
    home_value = db.Column(db.Float, nullable=True)
    multi_policy = db.Column(db.Boolean, nullable=False, default=False)
    premium = db.Column(db.Float, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    term_end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    customer = db.relationship("Customer")
    endorsements = db.relationship("Endorsement", backref="policy", lazy=True, cascade="all, delete-orphan")
    claims = db.relationship("Claim", backref="policy", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="policy", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "policy_number": self.policy_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer.full_name if self.customer else None,
            "product_type": self.product_type,
            "status": self.status,
            "driver_age": self.driver_age,
            "vehicle_year": self.vehicle_year,
            "vehicle_make": self.vehicle_make,
            "vehicle_model": self.vehicle_model,
            "vehicle_vin": self.vehicle_vin,
            "annual_mileage": self.annual_mileage,
            "usage_type": self.usage_type,
            "prior_claims_count": self.prior_claims_count,
            "coverage_type": self.coverage_type,
            "deductible": self.deductible,
            "anti_theft_device": self.anti_theft_device,
            "garaging_zip": self.garaging_zip,
            "home_value": self.home_value,
            "multi_policy": self.multi_policy,
            "premium": self.premium,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "term_end_date": self.term_end_date.isoformat() if self.term_end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


ENDORSEMENT_TYPES = ("coverage_change", "vehicle_update", "usage_update", "address_change", "driver_add")
# Which endorsement types are field-driven MTAs (edit real policy fields,
# premium recalculated automatically) vs. manual (no policy field currently
# models address/multi-driver data, so these stay a free-text description +
# manually-entered delta, same as before).
FIELD_DRIVEN_ENDORSEMENT_TYPES = ("coverage_change", "vehicle_update", "usage_update")


class Endorsement(db.Model):
    """A Mid-Term Adjustment (MTA) on a bound policy. For the field-driven
    types, field_changes records exactly what changed (old -> new) and
    premium_delta is computed by re-running calculate_premium() with the
    updated field(s) - not typed in by hand - so this is a real MTA, not
    just a logged note."""
    __tablename__ = "endorsements"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    policy_id = db.Column(db.String(36), db.ForeignKey("policies.id"), nullable=False)
    change_type = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)
    field_changes = db.Column(db.JSON, nullable=True)  # {"field": {"old": ..., "new": ...}, ...}
    premium_delta = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="applied")
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "change_type": self.change_type,
            "description": self.description,
            "field_changes": self.field_changes,
            "premium_delta": self.premium_delta,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


CLAIM_STATUSES = ("fnol", "under_review", "approved", "denied", "closed", "reopened")
CLAIM_INCIDENT_TYPES = ("collision", "theft", "weather", "liability", "fire", "vandalism", "other")

# Valid forward transitions for the E2E claims lifecycle (Jordan's adjuster
# workspace) - a real FNOL-to-closure process, not a free-choice dropdown.
# "reopened" lets a closed claim come back for review (e.g. a denied claim
# under appeal), and can itself move back into under_review.
CLAIM_TRANSITIONS = {
    "fnol": ("under_review",),
    "under_review": ("approved", "denied"),
    "approved": ("closed",),
    "denied": ("closed", "reopened"),
    "closed": ("reopened",),
    "reopened": ("under_review",),
}


class Claim(db.Model):
    __tablename__ = "claims"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    claim_number = db.Column(db.String(32), nullable=False, unique=True)
    policy_id = db.Column(db.String(36), db.ForeignKey("policies.id"), nullable=False)
    incident_date = db.Column(db.Date, nullable=False)
    incident_type = db.Column(db.String(20), nullable=True)  # collision|theft|weather|liability|fire|vandalism|other
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="fnol")
    adjuster_name = db.Column(db.String(255), nullable=True)
    estimated_amount = db.Column(db.Float, nullable=True)
    approved_amount = db.Column(db.Float, nullable=True)  # set on approval - may differ from the estimate
    denial_reason = db.Column(db.Text, nullable=True)  # required when status becomes "denied"
    # Audit trail of every status change: [{"status", "note", "changed_at"}, ...]
    # - a JSON column (same lightweight pattern as SQValex's own Defect model
    # uses for quality_findings) rather than a separate table, since this is
    # a training app and a full history table would be overkill here.
    status_history = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim_number": self.claim_number,
            "policy_id": self.policy_id,
            "incident_date": self.incident_date.isoformat() if self.incident_date else None,
            "incident_type": self.incident_type,
            "description": self.description,
            "status": self.status,
            "adjuster_name": self.adjuster_name,
            "estimated_amount": self.estimated_amount,
            "approved_amount": self.approved_amount,
            "denial_reason": self.denial_reason,
            "status_history": self.status_history,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    policy_id = db.Column(db.String(36), db.ForeignKey("policies.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="due")  # due | paid | missed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "amount": self.amount,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "status": self.status,
        }
