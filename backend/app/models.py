from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditMixin:
    """Common columns every table should have. Add this to any new model."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    server_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    operation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


ROLES = ["staff", "super_admin"]

# The three public-facing portals this back office reviews requests from.
PORTALS = ["employee", "pension", "vendor"]


class AdminUser(AuditMixin, Base):
    """A back-office staff account. Unlike the three public portals, this
    user is never also a citizen/employee/vendor record -- it's a
    separate identity with permissions over which portals' queues they
    may see and act on."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    staff_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="staff", nullable=False)

    # Per-module review permission. A "super_admin" account would
    # typically have all three set True; a "staff" account might only
    # cover one or two portals, matching a real back-office org chart.
    can_review_employee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_review_pension: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_review_vendor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AuditLog(AuditMixin, Base):
    """Immutable trail of what back-office staff did through this portal.
    This is the real compliance record for reviewer actions -- the
    underlying portal's own audit log only sees the shared service
    account, not the individual staff member."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_portal: Mapped[str | None] = mapped_column(String(20), nullable=True)  # employee | pension | vendor
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    before_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(String(20), default="Success", nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
