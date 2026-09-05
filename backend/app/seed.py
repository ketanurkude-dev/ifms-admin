from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import AdminUser


def seed_demo_accounts(db: Session) -> None:
    if db.query(AdminUser).count() > 0:
        return

    super_admin = AdminUser(
        staff_code="ADMIN001",
        name="Back Office Super Admin",
        email="superadmin@ifms.gov.in",
        mobile="9900000000",
        password_hash=hash_password("admin123"),
        role="super_admin",
        can_review_employee=True,
        can_review_pension=True,
        can_review_vendor=True,
    )
    db.add(super_admin)

    staff = AdminUser(
        staff_code="STAFF001",
        name="Employee Desk Staff",
        email="staff.employee@ifms.gov.in",
        mobile="9900000001",
        password_hash=hash_password("staff123"),
        role="staff",
        can_review_employee=True,
        can_review_pension=False,
        can_review_vendor=False,
    )
    db.add(staff)

    db.commit()
