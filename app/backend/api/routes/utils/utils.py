from datetime import time
from typing import Optional, List

from fastapi import Query  # type: ignore


class RouteQueryParams:
    def __init__(
        self,
        departure_time_from: Optional[time] = Query(
            None, description="Время отправления с (HH:MM)"
        ),
        departure_time_to: Optional[time] = Query(
            None, description="Время отправления до (HH:MM)"
        ),
        arrival_time_from: Optional[time] = Query(
            None, description="Время прибытия с (HH:MM)"
        ),
        arrival_time_to: Optional[time] = Query(
            None, description="Время прибытия до (HH:MM)"
        ),
        is_transfer: Optional[bool] = Query(
            None,
            description="Фильтр по маршрутам с пересадкой. "
            "True - только маршруты с пересадкой, "
            "False - только прямые маршруты",
        ),
        sites: Optional[List[int]] = Query(None, description="Список ID сайтов"),
    ):
        self.departure_time_from = departure_time_from
        self.departure_time_to = departure_time_to
        self.arrival_time_from = arrival_time_from
        self.arrival_time_to = arrival_time_to
        self.is_transfer = is_transfer
        self.sites = sites
