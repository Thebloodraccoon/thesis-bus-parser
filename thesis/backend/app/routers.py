from datetime import date, timezone
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from thesis.backend.app.auth import (
    AuthService,
    admin_only,
    analytic_or_admin,
    get_current_user,
    verify_refresh_token,
)
from thesis.backend.app.conf import get_db
from thesis.backend.app.exceptions import InvalidCredentialsException
from thesis.core.models import User
from thesis.backend.app.schemas import (
    CitySchema,
    FilterPreset,
    FilterPresetCreate,
    FilterPresetUpdate,
    Login,
    LogoutResponse,
    SiteCreate,
    SiteResponse,
    SiteUpdate,
    TaskBase,
    TaskResponse,
    TokenResponse,
    TripSchemaResponse,
    TwoFARequiredResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from thesis.backend.app.services import (
    CityService,
    FilterPresetService,
    RouteService,
    SiteService,
    TaskService,
    UserService,
)


# Auth
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/login",
    response_model=Union[TokenResponse, TwoFASetupResponse, TwoFARequiredResponse],
)
def login(request: Login, response: Response, db: Session = Depends(get_db)):
    svc = UserService(db)
    user = svc.get_by_email(request.email)
    if not user or not AuthService.verify_password(
        request.password, user.hashed_password
    ):
        raise InvalidCredentialsException()
    return AuthService.perform_login(user, db, response)


@auth_router.post("/2fa/verify", response_model=TokenResponse)
def verify_2fa(
    request: TwoFAVerifyRequest, response: Response, db: Session = Depends(get_db)
):
    return AuthService.finalize_2fa(request.otp_code, request.temp_token, db, response)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(http_request: Request, db: Session = Depends(get_db)):
    refresh_token = http_request.cookies.get("refresh_token", "")
    email = await verify_refresh_token(refresh_token, db)
    return {"access_token": AuthService.create_access_token({"sub": email})}


@auth_router.post("/logout", response_model=LogoutResponse)
async def logout(
    http_request: Request,
    response: Response,
    _: User = Depends(get_current_user),
):
    jwt_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")

    try:
        payload = AuthService.decode_token(jwt_token)
        exp = payload.get("exp")
        from datetime import datetime

        success = await AuthService.blacklist_token(
            jwt_token, datetime.fromtimestamp(exp, tz=timezone.utc)
        )
    except Exception as e:
        print(e)
        success = False

    refresh_token = http_request.cookies.get("refresh_token", "")
    if refresh_token:
        try:
            payload2 = AuthService.decode_token(refresh_token)
            from datetime import datetime

            await AuthService.blacklist_token(
                refresh_token, datetime.fromtimestamp(payload2["exp"], tz=timezone.utc)
            )
        except Exception as e:
            print(e)
            pass

    response.delete_cookie(
        key="refresh_token", httponly=True, samesite="none", secure=True
    )
    detail = "Logout successful" if success else "Token already invalid"

    return LogoutResponse(detail=detail)


# User
user_router = APIRouter(prefix="/user", tags=["Users"])


@user_router.get("/current", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@user_router.post("/invite-user", response_model=UserResponse)
async def invite_user(
    request: UserCreate, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    return await UserService(db).create(request)


@user_router.get("/list", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return UserService(db).get_all()


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    return UserService(db).get_by_id(user_id)


@user_router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    return UserService(db).update(user_id, updates.model_dump(exclude_unset=True))


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    UserService(db).delete(user_id)


# Site router
site_router = APIRouter(prefix="/sites", tags=["Sites"])


@site_router.get("/", response_model=List[SiteResponse])
async def get_all_sites(
    is_site_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await SiteService(db).get_cached(is_site_active)


@site_router.get("/{site_id}", response_model=SiteResponse)
def get_site_by_id(
    site_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return SiteService(db).get_by_id(site_id)


@site_router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: SiteCreate, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    svc = SiteService(db)
    site = svc.create(site_data)
    await svc.invalidate_cache()
    return site


@site_router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    svc = SiteService(db)
    site = svc.update(site_id, site_data)
    await svc.invalidate_cache()
    return site


@site_router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    svc = SiteService(db)
    svc.delete(site_id)
    await svc.invalidate_cache()


# City router
city_router = APIRouter(prefix="/cities", tags=["Cities"])


@city_router.get("/", response_model=List[CitySchema])
async def get_all_cities(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return await CityService(db).get_cached()


@city_router.post("/refresh-cache")
async def refresh_cities_cache(
    db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    await CityService(db).refresh_cache()
    return {"message": "Кеш міст успішно оновлено"}


# Task router
task_router = APIRouter(prefix="/celery/task", tags=["Celery Tasks"])


@task_router.get("/", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return TaskService(db).get_all()


@task_router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskBase, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    return TaskService(db).create(task_data)


@task_router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskBase,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    return TaskService(db).update(task_id, task_data)


@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)
):
    TaskService(db).delete(task_id)


# Filter preset router
preset_router = APIRouter(prefix="/presets", tags=["Presets"])


@preset_router.get("/", response_model=List[FilterPreset])
async def get_presets(
    db: Session = Depends(get_db), current_user: User = Depends(analytic_or_admin)
):
    return await FilterPresetService(db).get_all(current_user.id)


@preset_router.post("/", response_model=FilterPreset)
async def create_preset(
    preset: FilterPresetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(analytic_or_admin),
):
    return await FilterPresetService(db).create(current_user.id, preset)


@preset_router.patch("/{preset_id}", response_model=FilterPreset)
async def update_preset(
    preset_id: str,
    preset: FilterPresetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(analytic_or_admin),
):
    return await FilterPresetService(db).update(current_user.id, preset_id, preset)


@preset_router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(
    preset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(analytic_or_admin),
):
    await FilterPresetService(db).delete(current_user.id, preset_id)


# Route router
route_router = APIRouter(prefix="/routes", tags=["Routes"])


def _common_time_params(
    departure_time_from=Query(None),
    departure_time_to=Query(None),
    arrival_time_from=Query(None),
    arrival_time_to=Query(None),
    is_transfer: Optional[bool] = Query(None),
    sites: Optional[List[int]] = Query(None),
):
    return {
        "departure_time_from": departure_time_from,
        "departure_time_to": departure_time_to,
        "arrival_time_from": arrival_time_from,
        "arrival_time_to": arrival_time_to,
        "is_transfer": is_transfer,
        "sites": sites,
    }


@route_router.get("/routes-by-date")
def get_routes_by_date(
    departure_date: date = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    from_city_ids: Optional[List[int]] = Query(None),
    to_city_ids: Optional[List[int]] = Query(None),
    params: dict = Depends(_common_time_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return RouteService(db).get_all_routes(
        departure_date=departure_date,
        page=page,
        size=size,
        from_city_ids=from_city_ids,
        to_city_ids=to_city_ids,
        **params,
    )


@route_router.get("/route-by-cities")
def get_route_by_cities(
    from_city_id: int = Query(...),
    to_city_id: int = Query(...),
    departure_dates: List[date] = Query(...),
    params: dict = Depends(_common_time_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return RouteService(db).get_route_by_cities(
        from_city_id=from_city_id,
        to_city_id=to_city_id,
        departure_dates=departure_dates,
        **params,
    )


@route_router.get("/trips/", response_model=TripSchemaResponse)
def get_trips_by_route(
    route_id: int = Query(ge=1),
    params: dict = Depends(_common_time_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return RouteService(db).get_trips_by_route(route_id=route_id, **params)
