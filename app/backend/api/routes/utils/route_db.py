from datetime import date, time
from typing import Optional, List, Any, Dict, Set, Sequence

from sqlalchemy import select, func, literal_column, and_, Row  # type: ignore
from sqlalchemy.orm import Session, aliased  # type: ignore

from app.backend.api.routes.schema import TripSchemaResponse, RouteSchema
from app.backend.api.routes.utils.data_processing import create_route_entry, initialize_route_by_cities_result, \
    add_route_for_date, process_trips_result, process_routes_result
from app.backend.api.routes.utils.query_builders import get_available_sites, build_latest_history_subquery, \
    get_filtered_trip_subquery, is_transfer_condition
from app.core.models import RouteModel, TripModel, SiteModel, CityModel


class RouteCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_all_routes(
        self,
        departure_date: date,
        page: int = 0,
        size: int = 10,
        from_city_ids: Optional[List[int]] = None,
        to_city_ids: Optional[List[int]] = None,
        departure_time_from: Optional[time] = None,
        departure_time_to: Optional[time] = None,
        arrival_time_from: Optional[time] = None,
        arrival_time_to: Optional[time] = None,
        sites: Optional[List[int]] = None,
        is_transfer: Optional[bool] = None,
    ):
        available_sites = get_available_sites(sites)
        existing_sites = self._get_existing_sites(available_sites)

        unique_routes, total_count = self._get_unique_routes(
            departure_date, page, size, from_city_ids, to_city_ids
        )

        result = []
        for unique_route in unique_routes:
            from_city_id = unique_route.from_city_id
            to_city_id = unique_route.to_city_id

            route_entry = create_route_entry(
                from_city_id, to_city_id, departure_date, available_sites, existing_sites  # type: ignore
            )

            all_time_filters = (
                departure_time_from,
                departure_time_to,
                arrival_time_from,
                arrival_time_to,
            )

            routes = self._get_routes_data(  # type: ignore
                departure_date,
                from_city_id,  # type: ignore
                to_city_id,  # type: ignore
                available_sites,
                *all_time_filters,
                is_transfer,
            )

            for site_id in routes.keys():
                route_obj = routes[site_id]
                route_entry["agents"][str(site_id)] = route_obj

            result.append(route_entry)

        return {"total": total_count, "page": page, "size": size, "items": result}

    def get_route_by_cities(
        self,
        departure_dates: List[date],
        from_city_id: int,
        to_city_id: int,
        departure_time_from: Optional[time] = None,
        departure_time_to: Optional[time] = None,
        arrival_time_from: Optional[time] = None,
        arrival_time_to: Optional[time] = None,
        sites: Optional[List[int]] = None,
        is_transfer: Optional[bool] = None,
    ) -> Dict[str, Any]:
        available_sites = get_available_sites(sites)
        existing_sites = self._get_existing_sites(available_sites)
        existing_sites_str: Set[str] = set(str(site) for site in existing_sites)

        result: Dict[str, Any] = initialize_route_by_cities_result(
            from_city_id=from_city_id,
            to_city_id=to_city_id,
            departure_dates=departure_dates,
            available_sites=available_sites,
            existing_sites_str=existing_sites_str,
        )

        all_time_filters = (
            departure_time_from,
            departure_time_to,
            arrival_time_from,
            arrival_time_to,
        )

        for departure_date in departure_dates:
            date_str = str(departure_date)

            routes = self._get_routes_data(
                departure_date,
                from_city_id,
                to_city_id,
                available_sites,
                *all_time_filters,
                is_transfer,
            )

            add_route_for_date(result=result, routes=routes, date_str=date_str)

        return result

    def get_trips_data_by_route(
        self,
        route_id: int,
        departure_time_from: Optional[time] = None,
        departure_time_to: Optional[time] = None,
        arrival_time_from: Optional[time] = None,
        arrival_time_to: Optional[time] = None,
        is_transfer: Optional[bool] = None,
    ) -> TripSchemaResponse:
        latest_history_subs = build_latest_history_subquery()
        latest_history = latest_history_subs.alias("latest_history")

        filtered_trip_query = select(TripModel.id).where(TripModel.route_id == route_id)
        filtered_trip_ids = get_filtered_trip_subquery(
            filtered_trip_query,
            TripModel,
            departure_time_from,
            departure_time_to,
            arrival_time_from,
            arrival_time_to,
        )

        transfer_condition = is_transfer_condition(is_transfer)

        trips_query = (
            select(
                TripModel,
                RouteModel.departure_date.label("route_date"),
                latest_history.c.price,
                latest_history.c.currency,
                latest_history.c.available_seats,
                latest_history.c.created_at.label("price_updated_at"),
            )
            .select_from(TripModel)
            .where(TripModel.route_id == route_id)
            .where(TripModel.id.in_(select(filtered_trip_ids)))
            .where(transfer_condition)
            .join(latest_history)
            .join(RouteModel, TripModel.route_id == RouteModel.id)
        )

        trips_data = self.db.execute(trips_query).all()
        return process_trips_result(trips_data)

    def _get_existing_sites(self, available_sites: List[str]):
        existing_sites_query = select(SiteModel.id).where(
            SiteModel.id.in_(available_sites)
        )
        existing_sites = self.db.execute(existing_sites_query).scalars().all()
        return existing_sites

    def _get_unique_routes(
        self,
        departure_date: date,
        page: int,
        size: int,
        from_city_ids: Optional[List[int]] = None,
        to_city_ids: Optional[List[int]] = None,
    ) -> tuple[Sequence[Row[tuple[Any, Any, Any, Any]]], int | Any]:
        from_city = aliased(CityModel, name="from_city")
        to_city = aliased(CityModel, name="to_city")

        unique_routes_query = (
            select(
                from_city.name_ua.label("from_city_name"),
                to_city.name_ua.label("to_city_name"),
                RouteModel.from_city_id,
                RouteModel.to_city_id,
            )
            .join(from_city, RouteModel.from_city_id == from_city.id)
            .join(to_city, RouteModel.to_city_id == to_city.id)
            .group_by(
                RouteModel.from_city_id,
                RouteModel.to_city_id,
                from_city.name_ua,
                to_city.name_ua,
            )
            .where(RouteModel.departure_date == departure_date)
            .order_by(from_city.name_ua, to_city.name_ua)
        )

        if from_city_ids is not None:
            unique_routes_query = unique_routes_query.where(
                RouteModel.from_city_id.in_(from_city_ids)
            )

        if to_city_ids is not None:
            unique_routes_query = unique_routes_query.where(
                RouteModel.to_city_id.in_(to_city_ids)
            )

        count_query = select(func.count()).select_from(unique_routes_query.subquery())
        total_count = self.db.execute(count_query).scalar() or 0

        unique_routes_query = unique_routes_query.offset((page - 1) * size).limit(size)
        unique_routes = self.db.execute(unique_routes_query).all()

        return unique_routes, total_count

    def _get_routes_data(
        self,
        departure_date: date,
        from_city_id: int,
        to_city_id: int,
        available_sites: List[str],
        departure_time_from: Optional[time] = None,
        departure_time_to: Optional[time] = None,
        arrival_time_from: Optional[time] = None,
        arrival_time_to: Optional[time] = None,
        is_transfer: Optional[bool] = None,
    ) -> dict[Any, RouteSchema]:
        latest_history_subs = build_latest_history_subquery()
        latest_history = latest_history_subs.alias("latest_history")

        filtered_trip_query = select(TripModel.id).where(
            TripModel.route_id == RouteModel.id
        )
        filtered_trip_ids = get_filtered_trip_subquery(
            filtered_trip_query,
            TripModel,
            departure_time_from,
            departure_time_to,
            arrival_time_from,
            arrival_time_to,
        )

        transfer_condition = is_transfer_condition(is_transfer)

        sites_query = (
            select(
                RouteModel.from_city_id,
                RouteModel.to_city_id,
                RouteModel.site_id,
                RouteModel.departure_date,
                RouteModel.id,
                func.max(latest_history.c.currency).label("currency"),
                func.percentile_cont(0.5).within_group(latest_history.c.price).label("median_price"),
                func.min(latest_history.c.price).label("min_price"),
                func.max(latest_history.c.price).label("max_price"),
                func.count(func.distinct(TripModel.id)).label("total_segments_count"),
            )
            .outerjoin(
                TripModel,
                and_(
                    RouteModel.id == TripModel.route_id,
                    (
                        TripModel.id.in_(select(filtered_trip_ids))
                        if any([departure_time_from, departure_time_to, arrival_time_from, arrival_time_to])
                        else True
                    ),
                    transfer_condition,
                ),
            )
            .join(latest_history)
            .where(RouteModel.departure_date == departure_date)
            .where(RouteModel.from_city_id == from_city_id)
            .where(RouteModel.to_city_id == to_city_id)
            .where(RouteModel.site_id.in_(available_sites))
            .group_by(RouteModel.id)
        )

        routes_data = self.db.execute(sites_query).all()
        return process_routes_result(routes_data)
