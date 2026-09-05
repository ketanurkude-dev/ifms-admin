from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    frontend_origin: str = "http://localhost:7004"

    # Service-account credentials this portal uses to call each of the
    # three public-facing portals' existing /approver APIs on behalf of
    # whichever admin-portal user is logged in. Stands in for the real
    # OAuth2/mTLS service-to-service auth a production deployment would
    # use -- see app/integrations.py.
    # 127.0.0.1 rather than localhost: on Windows, httpx tries the ::1
    # (IPv6) resolution of "localhost" first and waits out a ~2s timeout
    # before falling back to IPv4, which made every one of these
    # service-account calls (and the review queue that fans out across
    # all of them) needlessly slow.
    employee_api_base: str = "http://127.0.0.1:9001"
    employee_service_employee_code: str
    employee_service_password: str

    pension_api_base: str = "http://127.0.0.1:9002"
    pension_service_ppo_number: str
    pension_service_password: str

    vendor_api_base: str = "http://127.0.0.1:9003"
    vendor_service_email: str
    vendor_service_password: str

    class Config:
        env_file = ".env"


settings = Settings()
