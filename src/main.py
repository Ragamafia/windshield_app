import asyncio

import uvicorn

from bot.bot import DetailerBot
from parser.parser import MainParser
from db.ctrl import db
from logger import logger
from config import cfg


async def run_bot():
    logger.info(f'DetailerBot started')
    bot = DetailerBot()
    await bot.run()

async def run_server():
    logger.info(f'App started')
    config = uvicorn.Config("app.app:app", host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

async def run_parser(db):
    logger.info(f'Parse process...')
    workers = []
    for _ in range(cfg.WORKERS_COUNT):
        workers.append(MainParser(db))
    await workers[0].ensure_brands()
    await asyncio.gather(*[worker.run() for worker in workers])


async def main():
    await db.setup_db()
    #await db.delete_user(1377785914)  # Admin
    #await db.delete_user(8082484525)  # Admin

    await run_parser(db)

    # server_task = asyncio.create_task(run_server())
    bot_task = asyncio.create_task(run_bot())
    await asyncio.gather(bot_task)


if __name__ == "__main__":
    asyncio.run(main())
