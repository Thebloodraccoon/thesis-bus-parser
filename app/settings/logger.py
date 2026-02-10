import base64
import os
import sys
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

# Flag for metric
METRICS_AVAILABLE = None

# Setting up a temporary zone
os.environ["TZ"] = "Europe/Kyiv"
time.tzset()

# Creation of a directory for logs
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

logger.add(
    LOGS_DIR / "app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    compression="zip",
)

# The path to the logs for compatibility
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
logs_dir = os.path.join(project_root, "logs")


def get_logger(name: Optional[str] = None):
    """He receives a logger with the specified name."""
    return logger.bind(name=name) if name else logger


def handle_processing_error(exception, departure_city, arrival_city, site_name):
    """Processing errors when processing routes."""

    exc_type = type(exception).__name__
    exc_msg = str(exception)

    if not exc_msg:
        error_info = f"{exc_type} (no detailed message)"
    else:
        error_info = f"{exc_type}: {exc_msg}"

    logger.error(
        f"Error processing route {departure_city.name_ru} -> {arrival_city.name_ru} | "
        f"{site_name}: {error_info}"
    )


def log_not_found_route(
    file_name,
    selected_date,
    departure_city,
    arrival_city,
    site_name,
    route,
    reason="Unknown",
):
    """Logs the route that was not found."""

    site_name = site_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    site_logs_dir = os.path.join(logs_dir, site_name)
    os.makedirs(site_logs_dir, exist_ok=True)

    log_file_path = os.path.join(site_logs_dir, file_name)

    headers = [
        "Timestamp",
        "Date",
        "Site Name",
        "Station IDs",
        "Trip ID",
        "Route ID",
        "Departure City",
        "Arrival City",
        "Reason",
        "Admin Link Trip ID",
        "LikeBus Link",
        "Route Link",
    ]

    try:
        # Safe access to trip_id
        if isinstance(route, dict):
            trip_id_raw = route.get("trip_id")
        else:
            trip_id_raw = getattr(route, "trip_id", None)

        if trip_id_raw and isinstance(trip_id_raw, list) and len(trip_id_raw) > 0:
            trip_id = base64.b64decode(trip_id_raw[0]).decode("utf-8").split("|")[1]
        else:
            trip_id = "unknown"

    except (KeyError, IndexError, UnicodeDecodeError, AttributeError):
        trip_id = "unknown"

    departure_city_name = getattr(departure_city, "name_ru", str(departure_city))
    arrival_city_name = getattr(arrival_city, "name_ru", str(arrival_city))

    # Safe access for other fields
    r_id = (
        route.get("id", "unknown")
        if isinstance(route, dict)
        else getattr(route, "id", "unknown")
    )
    r_tid = (
        route.get("trip_id", "unknown")
        if isinstance(route, dict)
        else getattr(route, "trip_id", "unknown")
    )
    r_rid = (
        route.get("route_id", "unknown")
        if isinstance(route, dict)
        else getattr(route, "route_id", "unknown")
    )

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        selected_date.strftime("%Y-%m-%d"),
        site_name,
        r_id,
        r_tid,
        r_rid,
        departure_city_name,
        arrival_city_name,
        reason,
        f"https://likebus.ua/admin/?a=bus_trip&set=edit&id={trip_id}",
        f"https://likebus.ua/ru/route/{departure_city_name.replace(' ', '')}/{arrival_city_name.replace(' ', '')}?from={departure_city_name.replace(' ', '+')}&to={arrival_city_name.replace(' ', '+')}&date={selected_date.strftime('%d.%m.%Y')}",
        f"https://likebus.ua/admin/?a=bus_route&set=edit&id={r_rid}",
    ]

    write_csv(log_file_path, headers, row)


def write_csv(file_path, headers, row):
    """Writes the line in the CSV file."""

    file_exists = os.path.exists(file_path)
    with open(file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(headers)

        writer.writerow(row)
