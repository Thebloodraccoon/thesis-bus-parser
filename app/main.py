from contextlib import asynccontextmanager

from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore

from app.auth.endpoints import router as auth_router
from app.settings import settings

from app.users.endpoints import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.Base.metadata.create_all(bind=settings.engine)
    yield
    print("Application is shutting down.")


app = FastAPI(
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/user", tags=["User"])
app.mount("/polonus", app=polonus)
