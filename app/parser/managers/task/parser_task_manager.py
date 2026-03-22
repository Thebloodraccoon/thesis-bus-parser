import asyncio
import os

from celery.exceptions import SoftTimeLimitExceeded

from app.parser.managers.parser.parser_manager import ParserManager
from app.parser.managers.task.base import BaseTaskManager
from app.parser.parsers.inbus.inbus_parser import InbusParser
from app.parser.parsers.rubikon.rubikon_parser import RubikonParser
from app.parser.parsers.ukrpas.ukrpas_parser import UkrpasParser
from app.parser.parsers.voyager.voyager_parser import VoyagerParser
from app.parser.schemas.types import ParsingConfig
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


def load_parsers():
    """Loads parsers from modules."""

    return {
        "ukrpas": UkrpasParser,
        "inbus": InbusParser,
        "rubikon": RubikonParser,
        "voyager": VoyagerParser,
    }


async def run_parser_with_timeout(
    parser,
    depth_from: int,
    depth_to: int,
    config: ParsingConfig,
    max_duration_seconds: int,
):
    """A compatible function for launching a parser with a timeout."""

    manager = ParserManager(parser, config)

    try:
        result = await asyncio.wait_for(
            manager.run_parser(depth_from, depth_to, max_duration_seconds),
            timeout=max_duration_seconds,
        )
        return result
    except asyncio.TimeoutError:
        logger.error(
            f"Parser exceeded the time limit in {max_duration_seconds} seconds and was stopped"
        )
        return {}
    except Exception as e:
        logger.error(f"Error when performing a parser: {e}")
        raise


class ParserTaskManager(BaseTaskManager):
    """Parsing task manager."""

    def __init__(self):
        super().__init__()
        self.parsers = load_parsers()

    @BaseTaskManager.task_wrapper(task_name="parser_task")
    async def run_parser(
        self,
        site_name: str,
        depth_from: int = 0,
        depth_to: int = 0,
        threads: int = 5,
        max_duration_seconds: int = 86400,
        use_proxy: bool = True,
    ):
        if depth_from < 0 or depth_to < depth_from:
            raise ValueError(f"Invalid depth range: {depth_from}-{depth_to}")

        parser_class = self.parsers.get(site_name)
        if not parser_class:
            raise ValueError(f"Unknown parser: {site_name}")

        logger.info(f"Running parser {site_name} | PID={os.getpid()}")

        try:
            parser = await parser_class.create()

            config = ParsingConfig(
                threads=threads,
                max_duration_seconds=max_duration_seconds,
                use_proxy=use_proxy,
            )

            result = await run_parser_with_timeout(
                parser, depth_from, depth_to, config, max_duration_seconds
            )

            result = result or {}

            total_routes = sum(getattr(c, "total_routes", 0) for c in result.values())
            total_errors = sum(getattr(c, "error_routes", 0) for c in result.values())

            self.metrics.record_parser_metrics(
                parser_name=site_name,
                site_name=site_name,
                routes_processed=total_routes,
                errors=total_errors,
                duration=0,
            )

            return result

        except SoftTimeLimitExceeded:
            logger.warning(f"Parser {site_name} exceeded time limit")
            self.metrics.record_parser_metrics(
                parser_name=site_name,
                site_name=site_name,
                routes_processed=0,
                errors=1,
                error_type="timeout",
            )
            raise
