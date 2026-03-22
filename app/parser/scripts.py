import asyncio

from app.parser.app import run_parser_with_timeout

from app.parser.schemas.types import ParsingConfig
from app.parser.parsers.ukrpas.ukrpas_parser import UkrpasParser


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