import httpx

from app.settings.logger import logger


def get_cities():
    city_endpoint = "https://likebus.ua/sync/v3/catalog/city"
    with httpx.Client(follow_redirects=True) as client:
        response = client.get(city_endpoint)
        cities = response.json()

    return cities


async def get_trip_by_id(trip_id, from_station_id, to_station_id, api_key):
    """Checks the availability of tickets for trip_id and stations."""

    trip_endpoint = "http://likebus.ua/sync/v3s/routes/trip"

    async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
        try:
            response = await client.get(
                trip_endpoint,
                headers={"x-api-key": api_key},
                params={
                    "from": int(from_station_id),
                    "to": int(to_station_id),
                    "id": trip_id,
                },
            )

            response_data = response.json()
            return response_data["list"]
        except Exception as e:
            logger.error(f"Error while checking trip: {e}")
            return None
