from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ParsingConfig:
    """Parsing configuration."""

    threads: int = 1
    max_duration_seconds: int = 3600
    time_interval: int = 60
    retry_attempts: int = 3
    timeout_seconds: int = 30
    use_proxy: bool = True


@dataclass
class ParsingCounters:
    """Counters for tracking the progress of parsing."""

    counter: int = 0
    total_routes: int = 0
    successful_routes: int = 0
    error_routes: int = 0


@dataclass
class RouteData:
    """Route data."""

    departure_city: str
    arrival_city: str
    route_id: int
    trip_id: List[str]
    from_date: datetime
    to_date: datetime
    departure_station_id: Optional[int] = None
    arrival_station_id: Optional[int] = None


@dataclass
class ParsingResult:
    """Parsing result."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: float = 0.0
    routes_processed: int = 0
