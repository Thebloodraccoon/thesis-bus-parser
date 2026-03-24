from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from thesis.backend.app.auth import AuthService
from thesis.backend.app.conf import engine, settings
from thesis.backend.app.routers import (
    auth_router,
    city_router,
    preset_router,
    route_router,
    site_router,
    task_router,
    user_router,
)
from thesis.core.models import User


def _init_admin(db: Session) -> None:
    """Creates a default administrator if one is absent."""

    if db.query(User).filter(User.email == settings.ADMIN_LOGIN).first():
        return

    admin = User(
        email=settings.ADMIN_LOGIN,
        hashed_password=AuthService.hash_password(settings.ADMIN_PASSWORD),
        role="admin",
        created_at=datetime.now(timezone.utc),
        is_2fa_enabled=False,
        otp_secret=None,
    )
    db.add(admin)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    with Session(engine) as db:
        _init_admin(db)

    yield
    print("Application is shutting down.")


app = FastAPI(
    title="Bus Ticket Aggregator API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(site_router)
app.include_router(city_router)
app.include_router(task_router)
app.include_router(preset_router)
app.include_router(route_router)


if __name__ == "__main__":
    uvicorn.run("thesis.backend.main:app", host="0.0.0.0", port=8000, reload=False)
