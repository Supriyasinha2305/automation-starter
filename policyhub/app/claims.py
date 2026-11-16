"""Shared E2E claims-lifecycle transition logic, used by both the JSON API
(routes_api.py) and the web adjuster workspace (routes_web.py) so the FNOL
-> under_review -> approved/denied -> closed process behaves identically
regardless of which surface a learner is practicing against."""
from datetime import datetime, timezone

from app.models import CLAIM_TRANSITIONS


class ClaimTransitionError(Exception):
    pass


def transition_claim(claim, new_status: str, note: str | None = None, adjuster_name: str | None = None,
                      approved_amount: float | None = None, denial_reason: str | None = None) -> None:
    """Moves claim.status forward along CLAIM_TRANSITIONS, validating the
    move is legal from the claim's current status, and appends an entry to
    claim.status_history - the audit trail an adjuster (or a QE writing
    state-transition test cases against it) can rely on."""
    allowed = CLAIM_TRANSITIONS.get(claim.status, ())
    if new_status not in allowed:
        raise ClaimTransitionError(
            f"Cannot move claim from '{claim.status}' to '{new_status}' - "
            f"valid next status(es): {', '.join(allowed) or 'none (terminal)'}"
        )
    if new_status == "denied" and not (denial_reason or "").strip():
        raise ClaimTransitionError("denial_reason is required when denying a claim")

    if adjuster_name:
        claim.adjuster_name = adjuster_name
    if new_status == "approved" and approved_amount is not None:
        claim.approved_amount = approved_amount
    if new_status == "denied":
        claim.denial_reason = denial_reason

    history = list(claim.status_history or [])
    history.append({
        "status": new_status,
        "note": note or None,
        "changed_at": datetime.now(timezone.utc).isoformat(),
    })
    claim.status_history = history
    claim.status = new_status
