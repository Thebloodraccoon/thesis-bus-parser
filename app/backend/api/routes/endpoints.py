from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.backend.api.auth.utils import get_current_user
from app.backend.api.routes.utils.route_db import RouteCRUD
from app.backend.api.routes.utils.utils import RouteQueryParams
from app.core.models import User
from app.backend.settings import settings, get_db

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("/routes-by-date")
def get_all_routes_by_date(
    departure_date: date = Query(
        ..., description="Date of departure in YYYY-MM-DD format"
    ),
    page: int = Query(1, ge=1, description="Page number, minimum 1"),
    size: int = Query(20, ge=1, le=100, description="Page size, from 1 to 100"),
    from_city_ids: Optional[List[int]] = Query(
        None, description="List of departure city IDs"
    ),
    to_city_ids: Optional[List[int]] = Query(
        None, description="List of arrival city IDs"
    ),
    common_params: RouteQueryParams = Depends(),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    routes = RouteCRUD(db).get_all_routes(
        page=page,
        size=size,
        departure_date=departure_date,
        from_city_ids=from_city_ids,
        to_city_ids=to_city_ids,
        departure_time_from=common_params.departure_time_from,
        departure_time_to=common_params.departure_time_to,
        arrival_time_from=common_params.arrival_time_from,
        arrival_time_to=common_params.arrival_time_to,
        is_transfer=common_params.is_transfer,
        sites=common_params.sites,
    )
    return routes


@router.get("/route-by-cities")
def get_route_by_cities(
    from_city_id: int = Query(description="ID города отправления"),
    to_city_id: int = Query(description="ID городов прибытия"),
    departure_dates: List[date] = Query(
        description="Список Дат отправления в формате YYYY-MM-DD"
    ),
    common_params: RouteQueryParams = Depends(),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    routes = RouteCRUD(db).get_route_by_cities(
        departure_dates=departure_dates,
        from_city_id=from_city_id,
        to_city_id=to_city_id,
        departure_time_from=common_params.departure_time_from,
        departure_time_to=common_params.departure_time_to,
        arrival_time_from=common_params.arrival_time_from,
        arrival_time_to=common_params.arrival_time_to,
        is_transfer=common_params.is_transfer,
        sites=common_params.sites,
    )
    return routes


@router.get("/trips/")
def get_trips_by_route(
    route_id: int = Query(ge=1, description="ID route"),
    common_params: RouteQueryParams = Depends(),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    trips = RouteCRUD(db).get_trips_data_by_route(
        route_id=route_id,
        departure_time_from=common_params.departure_time_from,
        departure_time_to=common_params.departure_time_to,
        arrival_time_from=common_params.arrival_time_from,
        arrival_time_to=common_params.arrival_time_to,
        is_transfer=common_params.is_transfer,
    )
    return trips
