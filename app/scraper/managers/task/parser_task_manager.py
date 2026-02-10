import asyncio
import os

from celery.exceptions import SoftTimeLimitExceeded

from app.scraper.managers.parser.parser_manager import ParserManager
from app.scraper.parsers.inbus.inbus_parser import InbusParser
from app.scraper.parsers.rubikon.rubikon_parser import RubikonParser
from app.scraper.parsers.ukrpas.ukrpas_parser import UkrpasParser
from app.scraper.parsers.voyager.voyager_parser import VoyagerParser
from app.scraper.schemas.types import ParsingConfig
from app.settings.logger import get_logger

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


class ParserTaskManager():
    """Parsing task manager."""

    def __init__(self):
        super().__init__()
        self.parsers = load_parsers()

    async def run_parser(
        self,
        site_name: str,
        depth_from: int = 0,
        depth_to: int = 0,
        threads: int = 5,
        max_duration_seconds: int = 86400,
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
            )

            result = await run_parser_with_timeout(
                parser, depth_from, depth_to, config, max_duration_seconds
            )

            result = result or {}
            return result

        except SoftTimeLimitExceeded:
            logger.warning(f"Parser {site_name} exceeded time limit")
            raise
