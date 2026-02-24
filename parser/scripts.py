import asyncio

from app.managers.task.parser_task_manager import run_parser_with_timeout

from app.schemas.types import ParsingConfig
from parser.app.managers.task import MaintenanceTaskManager
from parser.app.parsers.rubikon.rubikon_parser import RubikonParser
from parser.app.parsers.ukrpas.ukrpas_parser import UkrpasParser
from parser.app.parsers.voyager.voyager_parser import VoyagerParser


async def main():
    await run_parser_with_timeout(
        await UkrpasParser.create(),
        0,
        1,
        ParsingConfig(threads=10),
        5000
    )


if __name__ == "__main__":
    asyncio.run(main())