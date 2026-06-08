from datetime import UTC, datetime

from sqlmodel import select

from app.core.database import DBSession
from app.organization.models.organization import BillingStatus, Organization

ACTIVE_BILLING_STATUSES = [BillingStatus.ACTIVE, BillingStatus.ALWAYS_FREE]


def billing_status_active(status: BillingStatus, trial_expiry_dt: datetime | None) -> bool:
    """Return True if a billing status counts as active for data access.

    Active = ACTIVE, ALWAYS_FREE, or TRIAL whose trial has not yet expired (a null
    ``trial_expiry_dt`` is treated as not-yet-expired).
    """
    if status in ACTIVE_BILLING_STATUSES:
        return True
    if status == BillingStatus.TRIAL:
        return trial_expiry_dt is None or trial_expiry_dt > datetime.now(UTC)
    return False


def organization_billing_active(organization_id: int, db: DBSession) -> bool:
    """Return True if a single organization's billing status counts as active.

    Org-keyed gate for the public API, which has no authenticated user. An unknown
    organization id is treated as inactive (fail closed).
    """
    row = db.exec(
        select(Organization.billing_status, Organization.trial_expiry_dt).where(Organization.id == organization_id)
    ).first()
    if row is None:
        return False
    status, trial_expiry_dt = row
    return billing_status_active(status, trial_expiry_dt)
