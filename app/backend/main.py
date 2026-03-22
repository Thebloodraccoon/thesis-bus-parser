from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.backend.api.auth.endpoints import router as auth_router
from app.backend.api.celery.task.endpoints import router as celery_task_router
from app.backend.api.cities.endpoints import router as cities_router
from app.backend.api.routes.endpoints import router as route_router
from app.backend.api.sites.endpoints import router as site_router
from app.backend.api.users.endpoints import router as user_router
from app.backend.api.utils.auth_utils import pwd_context
from app.backend.settings import settings, Base, engine
from app.core.models import User


def init_default_admin(db: Session):
    user = db.query(User).filter(User.email == settings.ADMIN_LOGIN).first()

    if user:
        return

    hashed_pwd = pwd_context.hash(settings.ADMIN_PASSWORD)

    new_admin = User(
        email=settings.ADMIN_LOGIN,
        hashed_password=hashed_pwd,
        role="admin",
        created_at=datetime.now(timezone.utc),
        is_2fa_enabled=False,
        otp_secret=None
    )
    db.add(new_admin)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        init_default_admin(db)

    yield
    print("Application is shutting down.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(site_router)
app.include_router(cities_router)
app.include_router(celery_task_router)
app.include_router(route_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )