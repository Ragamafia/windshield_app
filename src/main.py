import asyncio
import time

import uvicorn

from bot.bot import DetailerBot
from parser.parser import MainParser
from logger import logger
from config import cfg


async def run_bot():
    bot = DetailerBot()
    logger.info(f'DetailerBot started')

    await bot.run()

async def run_server():
    config = uvicorn.Config("app.app:app", host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    logger.info(f'App started')

    await server.serve()

async def run_parser():
    parsers = []
    for _ in range(cfg.WORKERS_COUNT):
        parsers.append(MainParser())

    logger.info(f'Parse process...')
    start_time = time.time()

    await parsers[0].ensure_brands()
    await asyncio.gather(*[parser.run() for parser in parsers])

    end_time = time.time()
    logger.info(f'Parsing done. Times {end_time - start_time} seconds')


async def main():
    await run_parser()
    #await asyncio.get_event_loop().run_in_executor(None, run_parser)

    #server_task = asyncio.create_task(run_server())
    #bot_task = asyncio.create_task(run_bot())

    #await asyncio.gather(server_task, bot_task)


if __name__ == "__main__":
    asyncio.run(main())
