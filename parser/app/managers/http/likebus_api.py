import httpx


def get_cities():
    city_endpoint = "https://likebus.ua/sync/v3/catalog/city"
    with httpx.Client(follow_redirects=True) as client:
        response = client.get(city_endpoint)
        cities = response.json()

    return cities

