from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_token, decode_token, get_current_admin, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.events import log_action
from app.models import AdminUser
from app.schemas import AdminLoginIn, AdminRegisterIn, AdminUserOut, OtpVerifyIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: AdminRegisterIn, db: Session = Depends(get_db)):
    existing = (
        db.query(AdminUser)
        .filter(AdminUser.staff_code == payload.staff_code, AdminUser.is_deleted.is_(False))
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff code already registered")

    admin = AdminUser(
        staff_code=payload.staff_code,
        name=payload.name,
        email=payload.email,
        mobile=payload.mobile,
        password_hash=hash_password(payload.password),
        can_review_employee=payload.can_review_employee,
        can_review_pension=payload.can_review_pension,
        can_review_vendor=payload.can_review_vendor,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    log_action(db, actor_id=admin.id, actor_role=admin.role, action="Registered", entity_type="AdminUser", entity_id=admin.id)
    return {"message": "Registration successful. You can now log in."}


@router.post("/login", response_model=TokenOut)
def login(payload: AdminLoginIn, db: Session = Depends(get_db)):
    admin = (
        db.query(AdminUser)
        .filter(AdminUser.staff_code == payload.staff_code, AdminUser.is_deleted.is_(False))
        .first()
    )
    if not admin or not verify_password(payload.password, admin.password_hash):
        log_action(
            db, actor_id=admin.id if admin else None, actor_role=admin.role if admin else None,
            action="Failed login", entity_type="AdminUser", entity_id=admin.id if admin else None,
            result="Failure", details=f"Attempted login for {payload.staff_code}",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid staff code or password")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    pending_token = create_token(admin.staff_code, purpose="otp_pending", expires_minutes=5)
    log_action(db, actor_id=admin.id, actor_role=admin.role, action="Password verified", entity_type="AdminUser", entity_id=admin.id)
    return TokenOut(token_type="pending", pending_token=pending_token)


@router.post("/verify-otp", response_model=TokenOut)
def verify_otp(payload: OtpVerifyIn, db: Session = Depends(get_db)):
    if not payload.otp.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP must be 6 digits")

    staff_code = decode_token(payload.pending_token, expected_purpose="otp_pending")
    admin = (
        db.query(AdminUser)
        .filter(AdminUser.staff_code == staff_code, AdminUser.is_deleted.is_(False))
        .first()
    )
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin user not found")

    access_token = create_token(admin.staff_code, purpose="access", expires_minutes=settings.access_token_expire_minutes)
    log_action(db, actor_id=admin.id, actor_role=admin.role, action="Login", entity_type="AdminUser", entity_id=admin.id)
    return TokenOut(token_type="access", access_token=access_token)


@router.post("/logout")
def logout(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    log_action(db, actor_id=admin.id, actor_role=admin.role, action="Logout", entity_type="AdminUser", entity_id=admin.id)
    return {"message": "Logged out"}


@router.get("/me", response_model=AdminUserOut)
def me(admin: AdminUser = Depends(get_current_admin)):
    return admin
