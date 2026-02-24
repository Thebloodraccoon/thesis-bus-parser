from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth.endpoints import router as auth_router
from backend.app.api.celery.task.endpoints import router as celery_task_router
from backend.app.api.cities.endpoints import router as cities_router
from backend.app.api.routes.endpoints import router as route_router
from backend.app.api.sites.endpoints import router as site_router
from backend.app.api.users.endpoints import router as user_router
from backend.app.settings import settings


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
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(site_router)
app.include_router(cities_router)
app.include_router(celery_task_router)
app.include_router(route_router)

