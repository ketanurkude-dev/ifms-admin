from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.events import log_action
from app.integrations import PORTAL_LOGIN, fetch_queue, submit_review
from app.models import AdminUser
from app.schemas import QueueItemOut, ReviewActionIn

router = APIRouter(prefix="/queue", tags=["queue"])

PERMISSION_FIELD = {
    "employee": "can_review_employee",
    "pension": "can_review_pension",
    "vendor": "can_review_vendor",
}


def _allowed_portals(admin: AdminUser) -> list[str]:
    return [portal for portal, field in PERMISSION_FIELD.items() if getattr(admin, field)]


@router.get("", response_model=list[QueueItemOut])
def get_unified_queue(admin: AdminUser = Depends(get_current_admin)):
    """Pulls the pending-review queue from every portal this admin has
    permission for, live, and returns one combined list."""
    items = []
    for portal in _allowed_portals(admin):
        items.extend(fetch_queue(portal))
    items.sort(key=lambda item: item.get("application_date") or "", reverse=True)
    return items


@router.post("/review")
def review_item(
    payload: ReviewActionIn,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if payload.source_portal not in PORTAL_LOGIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown portal")
    if payload.source_portal not in _allowed_portals(admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not permitted to review this portal's requests")
    if payload.action not in ("Approved", "Rejected", "Returned"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    result = submit_review(payload.source_portal, payload.entity_type, payload.entity_id, payload.action, payload.remarks)

    log_action(
        db,
        actor_id=admin.id,
        actor_role=admin.role,
        source_portal=payload.source_portal,
        action=f"{payload.entity_type} {payload.action.lower()}",
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        after_value=payload.action,
        details=payload.remarks,
    )
    return result
