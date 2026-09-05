# Admin (Back Office) Portal -- context for future work

The 4th app in the IFMS prototype suite (alongside `emp_mgmt_pro`, `pension_mgmt`, `vendor_mgmt`
under `E:\IFMS`). Unlike the other three, this is **not** a public-facing self-service portal -- it
is an internal back-office login where staff review and decide requests raised on the three public
portals from a single unified queue, based on per-portal permissions.

## Why this exists
The project owner's own framing: the three portals are separately owned, separately implemented,
separately databased public-facing systems. In the real target architecture there would be a
separate admin/office login where staff -- depending on role/privileges -- see requests coming from
all three portals, validate/approve them, and the systems talk to each other over APIs. This app is
the prototype of that back office.

**Important, discussed explicitly with the project owner (2026-09-03):** this admin_portal build is
itself a demo/prototype. A *separate, real* admin portal is being developed independently by another
team, and it will eventually need to consume APIs from this system (with proper bearer-token auth).
The instruction was: build this one first, prove it out, and **then** decide whether/how the same
APIs get handed to that other real admin portal. Don't design around the other team's admin portal
yet -- just keep the API surface (JWT bearer auth, clean REST shapes) reasonable enough to be reused
later without a rewrite.

## Stack & ports
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL + **httpx** (new dependency vs. the other three --
  needed to call out to the other portals' REST APIs). Runs on **:9004**.
- Frontend: React (Vite) + Tailwind CSS, English-only (no i18n -- internal tool). Runs on **:7004**.
- DB: `postgresql+psycopg2://admin_db:admin_db@localhost:5432/admin_db` (see `backend/.env`). Its
  own database, entirely separate from the three portals' DBs.
- Venv at `backend/venv` (Windows). Start with:
  `cd E:\IFMS\admin_portal\backend && venv\Scripts\python.exe -m uvicorn app.main:app --port 9004`

## Architecture: how it reaches the three portals without changing them
**Zero changes were made to emp_mgmt_pro / pension_mgmt / vendor_mgmt to build this.** Instead,
`app/integrations.py` holds **service-account credentials** for one already-existing reviewer/
approver account per portal (configured in `backend/.env`: `EMPLOYEE_SERVICE_*`,
`PENSION_SERVICE_*`, `VENDOR_SERVICE_*`). At request time it:

1. Logs into that portal's own `/auth/login` + `/auth/verify-otp` (same two-step JWT pattern every
   portal uses; OTP is mocked, `_OTP = "123456"` always works), caching the resulting access token
   in memory (`_token_cache`, ~100 min TTL, refreshed on a 401).
2. Calls that portal's existing `/approver/*` endpoints with `Authorization: Bearer <token>`.
3. Normalizes each portal's differently-shaped queue response into a common `QueueItemOut` shape
   (`source_portal`, `entity_type`, `entity_id`, `title`, `applicant_name`, `status`,
   `application_date`, `raw`) via `_normalize_item()`.

This stands in for real OAuth2/mTLS service-to-service auth a production deployment would use
between separately-owned systems. **The tradeoff, explicitly accepted:** the underlying portal's own
audit log will show the shared service account as the actor, not the individual admin-portal staff
member who made the call. This app's *own* `AuditLog` table is the true compliance record of who
(which human) did what -- see `app/routers/queue.py`'s `review_item`, which logs the action here
*and* forwards it to the source portal.

`QUEUE_ENDPOINTS` in `integrations.py` maps each portal + entity_type to its queue path and review
path. **If any of the three portals' `/approver/*` routes change shape, this map (and
`_normalize_item`) must be updated to match** -- there's no schema contract enforcing it, since the
whole point was avoiding changes to those three apps.

| Portal   | Queue endpoint(s)                                  | entity_types              | Review endpoint(s) |
|----------|-----------------------------------------------------|----------------------------|---------------------|
| employee | `GET /approver/queue`                               | `request`, `certificate`  | `POST /approver/{kind}/{id}/review` |
| pension  | `GET /approver/queue`                               | `bank_request`, `benefit_claim` | `POST /approver/bank-requests/{id}/review`, `POST /approver/benefit-claims/{id}/review` |
| vendor   | `GET /approver/applications`, `GET /approver/profile-changes` | `application`, `profile_change` | `POST /approver/applications/{id}/review`, `POST /approver/profile-changes/{id}/review` |

Review action values: `Approved` / `Rejected` / `Returned` -- but vendor's `profile_change` only
accepts `Approved`/`Rejected` (no "Returned"); submitting "Returned" there surfaces that portal's
400 error back to the admin-portal user as-is.

## Data model (`app/models.py`)
- `AdminUser` -- back-office staff identity, separate from any portal's own user records. Has
  per-module **boolean** permission columns: `can_review_employee`, `can_review_pension`,
  `can_review_vendor` (kept native `Boolean`, per the project-wide "never convert bools to Y/N"
  decision -- see `emp_mgmt_pro/CONTEXT.md` for why). `role` is `"staff"` or `"super_admin"`.
- `AuditLog` -- this portal's own compliance trail, with a `source_portal` column (`employee` /
  `pension` / `vendor` / null for admin-portal-only actions like login/logout).
- Both carry the standard `AuditMixin` (`is_active`, `is_deleted`, `server_date`, `operation_date`).

## Key backend modules
- `app/auth.py` -- same JWT helper shape as the other three portals (`create_token`, `decode_token`,
  bcrypt hash/verify), but `get_current_admin` / `require_super_admin` instead of
  `get_current_employee` / `require_approver`.
- `app/routers/auth.py` -- `/auth/register`, `/auth/login`, `/auth/verify-otp`, `/auth/logout`,
  `/auth/me` (returns `AdminUserOut` -- used by the frontend to show the logged-in admin's name/role/
  permissions).
- `app/routers/queue.py` -- `GET /queue` (unified, live-pulled queue filtered to portals the admin
  has permission for) and `POST /queue/review` (permission-checked, forwards to
  `integrations.submit_review`, then writes this portal's own audit log entry).
- `app/routers/audit.py` -- same search/CSV-export pattern as the other three portals, with
  `source_portal` as an extra filter dimension instead of a `<portal>_id` filter.
- `app/seed.py` -- seeds two demo `AdminUser` rows on first startup if the table is empty (see
  below).

## Frontend notes
- No i18n -- internal tool, English only, unlike the three public portals.
- `src/pages/Queue.jsx` -- the main dashboard: cards per pending item, portal filter dropdown,
  inline expand-to-review panel (remarks textarea + Approve/Reject/Return buttons).
- `src/pages/AppLayout.jsx` -- sidebar shows the logged-in admin's per-portal permissions (from
  `/auth/me`) so it's visually obvious which queues they can act on.
- **The `/queue` call is genuinely slow (~9-10s)** the first time per session, because it does
  sequential httpx round-trips (service login + queue fetch) across up to 3 portals x up to 2
  endpoints each; subsequent calls are faster once tokens are cached in `_token_cache`. The frontend
  has no explicit timeout set on axios, so it will eventually resolve -- but if this becomes
  annoying, consider parallelizing the per-portal calls in `integrations.fetch_queue` (e.g. with
  `httpx.AsyncClient` + `asyncio.gather`) rather than adding a spinner as a band-aid.
- No `postForm`/file-upload helper (not needed here -- this app doesn't handle document uploads).

## Demo accounts
Seeded automatically on first backend startup (`app/seed.py`) if `admin_users` is empty:
- `ADMIN001` / `admin123` -- role `super_admin`, all three `can_review_*` flags true.
- `STAFF001` / `staff123` -- role `staff`, only `can_review_employee` true.

## Service-account credentials this app depends on (in the *other* portals)
These must keep existing and keep working, or `integrations.py` logins will fail with a 502:
- Employee: `employee_code=DDOTEST001`, password `test123` (DDO/HOD role).
- Pension: `ppo_number=PPO/2026/OFFICER1`, password `test123` (approver role).
- Vendor: `email=reviewer@vendor.gov.in`, password `reviewer123` (auto-seeded reviewer account).

## Status (as of 2026-09-03)
Backend and frontend both built and verified end-to-end through the actual browser UI: admin login
-> OTP -> unified queue (confirmed it pulls real pending items from the employee and pension
portals) -> approve an item through the UI -> confirmed via direct `psql` query that the underlying
employee portal's own database was actually mutated (status, generated certificate number, review
remarks all correct) -- not just a local admin-portal state change. Audit logging on this portal's
own side also confirmed via API. Not yet done: adding any link to this portal from the public
landing page (deliberately -- it's an internal tool, this needs to be a separate decision, not
assumed), and no decision yet on exposing these APIs to the other, separately-developed real admin
portal (see "Why this exists" above -- explicitly deferred until this prototype is proven out).

## Related
`E:\IFMS\emp_mgmt_pro\CONTEXT.md`, `E:\IFMS\pension_mgmt\CONTEXT.md`, `E:\IFMS\vendor_mgmt\CONTEXT.md`
for the three portals this app integrates with, and `E:\IFMS\TESTING_GUIDE.md` for broader
cross-portal test steps.
