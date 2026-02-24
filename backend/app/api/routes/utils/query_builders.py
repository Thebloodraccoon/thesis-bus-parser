from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import desc, select, func, or_, Time, and_  # type: ignore

from backend.app.api.models import TripHistoryModel, TripModel


def get_available_sites(sites: Optional[List[int]] = None) -> List[str]:
    if sites is not None:
        return [str(site) for site in sites]

    return []


def build_latest_history_subquery():
    cutoff_date = datetime.now() - timedelta(days=30)

    return (
        select(
            TripHistoryModel.trip_id,
            TripHistoryModel.price,
            TripHistoryModel.currency,
            TripHistoryModel.available_seats,
            TripHistoryModel.created_at,
        )
        .where(TripHistoryModel.trip_id == TripModel.id)
        .where(TripHistoryModel.created_at >= cutoff_date)
        .order_by(desc(TripHistoryModel.created_at))
        .limit(1)
        .correlate(TripModel)
        .lateral()
    )


def apply_time_filters(
    query,
    trip_model,
    departure_time_from=None,
    departure_time_to=None,
    arrival_time_from=None,
    arrival_time_to=None,
):

    if departure_time_from is not None:
        query = query.where(
            func.cast(trip_model.departure_time, Time) >= departure_time_from
        )

    if departure_time_to is not None:
        query = query.where(
            func.cast(trip_model.departure_time, Time) <= departure_time_to
        )

    if arrival_time_from is not None:
        query = query.where(
            func.cast(trip_model.arrival_time, Time) >= arrival_time_from
        )

    if arrival_time_to is not None:
        query = query.where(func.cast(trip_model.arrival_time, Time) <= arrival_time_to)

    return query


def get_filtered_trip_subquery(
    filtered_trip_query,
    trip_model,
    departure_time_from=None,
    departure_time_to=None,
    arrival_time_from=None,
    arrival_time_to=None,
):
    if any(
        [departure_time_from, departure_time_to, arrival_time_from, arrival_time_to]
    ):
        filtered_trip_query = apply_time_filters(
            filtered_trip_query,
            trip_model,
            departure_time_from,
            departure_time_to,
            arrival_time_from,
            arrival_time_to,
        )

    return filtered_trip_query.subquery()


def is_transfer_condition(is_transfer: Optional[bool]):
    if is_transfer is not None:
        return TripModel.is_transfer == is_transfer
    return True
