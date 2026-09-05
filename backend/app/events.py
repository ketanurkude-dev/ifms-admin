import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    actor_id: int | None,
    actor_role: str | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    source_portal: str | None = None,
    before_value: str | None = None,
    after_value: str | None = None,
    result: str = "Success",
    details: str | None = None,
):
    entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        source_portal=source_portal,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_value=before_value,
        after_value=after_value,
        result=result,
        correlation_id=uuid.uuid4().hex[:12],
        details=details,
    )
    db.add(entry)
    db.commit()
    return entry
