from app.parser.db.city_db import city_crud
from app.parser.managers.currency.currency_manager import CurrencyManager
from app.parser.managers.task.base import BaseTaskManager
from app.parser.parsers.inbus.inbus_city_parser import InbusCityParser
from app.parser.parsers.rubikon.rubikon_city_parser import RubikonCityParser
from app.parser.parsers.ukrpas.ukrpas_city_parser import UkrPasCityParser
from app.parser.parsers.voyager.voyager_city_parser import VoyagerCityParser
from app.parser.settings.conf import get_db
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


class MaintenanceTaskManager(BaseTaskManager):
    """Manager for maintenance tasks."""

    @BaseTaskManager.task_wrapper(task_name="city_update")
    async def run_city_update_task(self):
        """Fulfills the task of updating cities."""

        logger.info("Starting weekly update for cities and stations.")

        with get_db() as db:
            city_crud.save_cities(db)

        # Bulk Parsers
        await InbusCityParser().run()
        await VoyagerCityParser().run()

        # API Parsers
        await UkrPasCityParser().run()
        await RubikonCityParser().run()

        message = "Weekly update for cities and stations completed."
        logger.info(message)
        return message

    @BaseTaskManager.task_wrapper(task_name="currency_update")
    async def run_currency_update_task(self):
        """Fulfills the task of updating currencies."""

        result = await CurrencyManager().fetch_and_update_currencies()
        return f"Updated {len(result)} currencies"
