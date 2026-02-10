from app.scraper.db.city_db import city_crud
from app.scraper.managers.currency.currency_manager import CurrencyManager
from app.scraper.parsers.inbus.inbus_city_parser import InbusCityParser
from app.scraper.parsers.rubikon.rubikon_city_parser import RubikonCityParser
from app.scraper.parsers.ukrpas.ukrpas_city_parser import UkrPasCityParser
from app.scraper.parsers.voyager.voyager_city_parser import VoyagerCityParser
from app.settings.conf import get_db
from app.settings.logger import get_logger

logger = get_logger(__name__)


class MaintenanceTaskManager:
    """Manager for maintenance tasks."""

    @classmethod
    async def run_city_update_task(cls):
        """Fulfills the task of updating cities."""

        logger.info("Starting weekly update for cities and stations.")

        with get_db() as db:
            city_crud.save_cities(db)

        # Bulk Parsers
        await VoyagerCityParser().run()
        await InbusCityParser().run()
        await RubikonCityParser().run()
        await UkrPasCityParser().run()

        message = "Weekly update for cities and stations completed."
        logger.info(message)
        return message

    @classmethod
    async def run_currency_update_task(cls):
        """Fulfills the task of updating currencies."""

        result = await CurrencyManager().fetch_and_update_currencies()
        return f"Updated {len(result)} currencies"
