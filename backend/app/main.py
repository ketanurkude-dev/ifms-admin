from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import audit, auth, queue
from app.seed import seed_demo_accounts

# Creates tables on startup if they don't exist yet (simple approach, no migrations tool).
Base.metadata.create_all(bind=engine)


def _seed() -> None:
    db = SessionLocal()
    try:
        seed_demo_accounts(db)
    finally:
        db.close()


_seed()

app = FastAPI(title="Admin (Back Office) Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(queue.router)
app.include_router(audit.router)


@app.get("/")
def root():
    return {"status": "ok"}
