import asyncio

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
    workers = []
    for _ in range(cfg.WORKERS_COUNT):
        workers.append(MainParser())

    logger.info(f'Parse process...')
    await workers[0].ensure_brands()
    await asyncio.gather(*[worker.run() for worker in workers])


async def main():
    await run_parser()

    #server_task = asyncio.create_task(run_server())
    #bot_task = asyncio.create_task(run_bot())

    #await asyncio.gather(server_task, bot_task)


if __name__ == "__main__":
    asyncio.run(main())
