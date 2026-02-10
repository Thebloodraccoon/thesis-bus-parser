from datetime import date
from typing import List, Dict, Any, Optional

from app.scraper.logger import get_logger
from app.settings import settings
from app.scraper.db.currency_db import update_or_create_currency
from app.scraper.schemas.currency_schema import CurrencySchema
from app.scraper.managers.http import send_request

logger = get_logger(__name__)


class CurrencyManager:
    """A service that is responsible for the business logic of working with currencies."""

    def __init__(self):
        self.nbu_api_url = (
            "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
        )
        self.byn_api_url = "https://minfin.com.ua/api/coin/graph/byn/uah"

    async def fetch_and_update_currencies(self) -> List[Dict[str, Any]]:
        """Receives courses and updates the database. Returns a list of updated currencies."""

        nbu_currency_data = await self._get_nbu_currencies()
        byn_rate = await self._get_byn_rate()

        return self.process_all_currency_data(nbu_currency_data, byn_rate)

    async def _get_nbu_currencies(self) -> List[Dict[str, Any]]:
        """Receives data on currencies from the NBU API."""

        response = await send_request(
            url=self.nbu_api_url,
            method="GET",
            params={"json": ""},
        )
        return response.json()

    async def _get_byn_rate(self) -> Optional[float]:
        try:
            today_str = date.today().strftime("%Y-%m-%d")
            url = f"{self.byn_api_url}/{today_str}/{today_str}/days/"

            response = await send_request(url=url, method="GET")
            data = response.json()

            if not data.get("data"):
                return None

            rate = data["data"][-1].get("course", {}).get("banks", {}).get("bid")
            return float(rate) if rate and rate != "-" else None

        except Exception as e:
            logger.warning(f"Failed to fetch BYN rate: {e}")
            return None

    def process_all_currency_data(
        self, nbu_data: List[Dict[str, Any]], byn_rate: Optional[float]
    ) -> List[Dict[str, Any]]:
        """Processes all the data of the currencies and saves it into the database."""

        updated = []
        with settings.get_db() as db:
            for item in nbu_data:
                if res := self._process_currency(
                    db, item.get("cc"), item.get("rate"), item.get("exchangedate")
                ):
                    updated.append(res)

            if byn_rate:
                if res := self._process_currency(db, "BYN", byn_rate):
                    updated.append(res)
        return updated

    def _process_currency(self, db, code, rate, date_str=None) -> Optional[Dict]:
        """Processing one currency from the NBU."""

        try:
            ex_date = self._parse_date(date_str) if date_str else date.today()
            schema = CurrencySchema(code=code, rate=float(rate), exchange_date=ex_date)
            currency = update_or_create_currency(db, schema)

            return {
                "code": currency.code,
                "rate": currency.rate,
                "date": str(currency.exchange_date),
            }
        except Exception as e:
            logger.error(f"Error processing {code}: {e}")
            return None

    @staticmethod
    def _parse_date(date_str: str) -> date:
        try:
            d, m, y = date_str.split(".")
            return date(int(y), int(m), int(d))
        except (ValueError, AttributeError):
            return date.today()
