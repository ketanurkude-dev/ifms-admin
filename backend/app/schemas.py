from datetime import datetime

from pydantic import BaseModel, EmailStr


class AdminRegisterIn(BaseModel):
    staff_code: str
    name: str
    email: EmailStr
    mobile: str
    password: str
    can_review_employee: bool = False
    can_review_pension: bool = False
    can_review_vendor: bool = False


class AdminLoginIn(BaseModel):
    staff_code: str
    password: str


class OtpVerifyIn(BaseModel):
    pending_token: str
    otp: str


class TokenOut(BaseModel):
    token_type: str
    access_token: str | None = None
    pending_token: str | None = None


class AdminUserOut(BaseModel):
    id: int
    staff_code: str
    name: str
    email: str
    mobile: str
    role: str
    can_review_employee: bool
    can_review_pension: bool
    can_review_vendor: bool

    class Config:
        from_attributes = True


class QueueItemOut(BaseModel):
    """One request/application/grievance pulled live from a portal's
    /approver queue, normalized to a common shape for the unified
    dashboard."""

    source_portal: str
    entity_type: str
    entity_id: int
    title: str
    applicant_name: str | None = None
    status: str | None = None
    application_date: str | None = None
    details: list[dict] = []
    raw: dict


class ReviewActionIn(BaseModel):
    source_portal: str
    entity_type: str
    entity_id: int
    action: str  # Approved | Rejected | Returned (meaning depends on entity_type)
    remarks: str | None = None


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None
    actor_role: str | None
    source_portal: str | None
    action: str
    entity_type: str
    entity_id: int | None
    before_value: str | None
    after_value: str | None
    result: str
    correlation_id: str | None
    details: str | None
    server_date: datetime

    class Config:
        from_attributes = True
