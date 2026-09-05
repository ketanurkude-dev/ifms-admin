"""Talks to the three public-facing portals (employee, pension, vendor) as
a shared service account, so this back-office portal can pull their
approver queues and submit review decisions without those portals'
code changing at all.

Each portal already has its own two-step login (password -> pending_token
-> OTP -> access_token). We log in as a demo reviewer/approver account
that already exists in that portal, cache the resulting access token in
memory, and reuse it until the portal rejects it. This stands in for the
real OAuth2/mTLS service-to-service auth a production deployment would
use between separately-owned systems.
"""

from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException, status

from app.config import settings

_OTP = "123456"  # every portal's OTP step is mocked and accepts any 6 digits

PORTAL_LOGIN = {
    "employee": {
        "base_url": settings.employee_api_base,
        "login_field": "employee_code",
        "login_value": settings.employee_service_employee_code,
        "password": settings.employee_service_password,
    },
    "pension": {
        "base_url": settings.pension_api_base,
        "login_field": "ppo_number",
        "login_value": settings.pension_service_ppo_number,
        "password": settings.pension_service_password,
    },
    "vendor": {
        "base_url": settings.vendor_api_base,
        "login_field": "email",
        "login_value": settings.vendor_service_email,
        "password": settings.vendor_service_password,
    },
}

# entity_type -> (queue path, review path template, field the queue item's id comes from)
QUEUE_ENDPOINTS = {
    "employee": [
        {"entity_type": "request", "path": "/approver/queue", "review_path": "/approver/request/{id}/review"},
        {"entity_type": "certificate", "path": "/approver/queue", "review_path": "/approver/certificate/{id}/review"},
    ],
    "pension": [
        {"entity_type": "bank_request", "path": "/approver/queue", "review_path": "/approver/bank-requests/{id}/review"},
        {"entity_type": "benefit_claim", "path": "/approver/queue", "review_path": "/approver/benefit-claims/{id}/review"},
    ],
    "vendor": [
        {"entity_type": "application", "path": "/approver/applications", "review_path": "/approver/applications/{id}/review"},
        {"entity_type": "profile_change", "path": "/approver/profile-changes", "review_path": "/approver/profile-changes/{id}/review"},
    ],
}

_token_cache: dict[str, dict] = {}
_TOKEN_LIFETIME = timedelta(minutes=100)


def _login(portal: str) -> str:
    cfg = PORTAL_LOGIN[portal]
    with httpx.Client(base_url=cfg["base_url"], timeout=10) as client:
        login_resp = client.post(
            "/auth/login", json={cfg["login_field"]: cfg["login_value"], "password": cfg["password"]}
        )
        if login_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not sign in to the {portal} portal's service account",
            )
        pending_token = login_resp.json()["pending_token"]

        otp_resp = client.post(
            "/auth/verify-otp", json={"pending_token": pending_token, "otp": _OTP}
        )
        if otp_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OTP verification failed for the {portal} portal's service account",
            )
        return otp_resp.json()["access_token"]


def get_service_token(portal: str, force_refresh: bool = False) -> str:
    cached = _token_cache.get(portal)
    if cached and not force_refresh and datetime.utcnow() < cached["expires_at"]:
        return cached["token"]

    token = _login(portal)
    _token_cache[portal] = {"token": token, "expires_at": datetime.utcnow() + _TOKEN_LIFETIME}
    return token


def _request(portal: str, method: str, path: str, **kwargs) -> httpx.Response:
    cfg = PORTAL_LOGIN[portal]
    token = get_service_token(portal)
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=cfg["base_url"], timeout=10) as client:
        resp = client.request(method, path, headers=headers, **kwargs)
        if resp.status_code == 401:
            token = get_service_token(portal, force_refresh=True)
            headers = {"Authorization": f"Bearer {token}"}
            resp = client.request(method, path, headers=headers, **kwargs)
        return resp


def fetch_queue(portal: str) -> list[dict]:
    """Pull every pending item for a portal, tagged with entity_type so the
    review endpoint knows which of that portal's APIs to call back into."""
    endpoints = QUEUE_ENDPOINTS.get(portal, [])
    seen_paths: set[str] = set()
    items: list[dict] = []

    for endpoint in endpoints:
        if endpoint["path"] in seen_paths:
            continue
        seen_paths.add(endpoint["path"])

        resp = _request(portal, "GET", endpoint["path"])
        if resp.status_code != 200:
            continue
        for raw in resp.json():
            entity_type = raw.get("kind") or raw.get("item_type") or endpoint["entity_type"]
            items.append(_normalize_item(portal, entity_type, raw))

    return items


def _detail_pairs(pairs: list[tuple[str, object]]) -> list[dict]:
    """Turns a list of (label, value) tuples into the shape the frontend
    renders as a detail list, dropping anything blank so a reviewer only
    sees fields that actually have a value."""
    return [{"label": label, "value": value} for label, value in pairs if value not in (None, "")]


def _normalize_item(portal: str, entity_type: str, raw: dict) -> dict:
    if portal == "employee":
        details = _detail_pairs(
            [
                ("Employee", raw.get("employee_name")),
                ("Designation", raw.get("employee_designation")),
                ("Office", raw.get("employee_office")),
                ("Description" if entity_type == "request" else "Purpose", raw.get("description")),
                ("Amount", raw.get("amount")),
            ]
        )
        return {
            "source_portal": portal,
            "entity_type": entity_type,
            "entity_id": raw["id"],
            "title": raw.get("title", ""),
            "applicant_name": raw.get("employee_name"),
            "status": raw.get("status"),
            "application_date": raw.get("server_date"),
            "details": details,
            "raw": raw,
        }
    if portal == "pension":
        details = _detail_pairs(
            [
                ("Pensioner", raw.get("pensioner_name")),
                ("PPO number", raw.get("ppo_number")),
                ("Reason" if entity_type == "bank_request" else "Details", raw.get("description")),
                ("New account number", raw.get("new_account_number")),
                ("New IFSC", raw.get("new_ifsc")),
                ("Due date", raw.get("due_date")),
            ]
        )
        return {
            "source_portal": portal,
            "entity_type": entity_type,
            "entity_id": raw["id"],
            "title": raw.get("title", ""),
            "applicant_name": raw.get("pensioner_name"),
            "status": raw.get("status"),
            "application_date": raw.get("server_date"),
            "details": details,
            "raw": raw,
        }
    # vendor
    if entity_type == "application":
        title = f"Vendor registration: {raw.get('company_name', '')}"
        details = _detail_pairs(
            [
                ("Vendor type", raw.get("vendor_type")),
                ("Company", raw.get("company_name")),
                ("Contact person", raw.get("contact_person_name")),
                ("Email", raw.get("email")),
                ("Mobile", raw.get("mobile")),
                ("Address", raw.get("address")),
                ("PAN", raw.get("pan_number")),
                ("GSTIN", raw.get("gstin_number")),
                ("Application reference", raw.get("application_reference")),
            ]
        )
    else:
        title = f"Profile change: {raw.get('field_name', '')}"
        details = _detail_pairs(
            [
                ("Field", raw.get("field_name")),
                ("Current value", raw.get("old_value")),
                ("Requested value", raw.get("new_value")),
                ("Reason", raw.get("reason")),
            ]
        )
    return {
        "source_portal": portal,
        "entity_type": entity_type,
        "entity_id": raw["id"],
        "title": title,
        "applicant_name": raw.get("company_name"),
        "status": raw.get("status"),
        "application_date": raw.get("server_date"),
        "details": details,
        "raw": raw,
    }


def submit_review(portal: str, entity_type: str, entity_id: int, action: str, remarks: str | None) -> dict:
    endpoints = QUEUE_ENDPOINTS.get(portal, [])
    matched = next((e for e in endpoints if e["entity_type"] == entity_type), None)
    if not matched:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown entity type for this portal")

    path = matched["review_path"].format(id=entity_id)
    resp = _request(portal, "POST", path, json={"status": action, "review_remarks": remarks})
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The {portal} portal rejected the review: {resp.text}",
        )
    return resp.json()
