import asyncio

import uvicorn

from utils import checker
from db.ctrl import db
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

async def download_image():
    logger.info(f'Download images...')
    semaphore = asyncio.Semaphore(100)
    cars = await db.get_images_for_check()
    async with semaphore:
        tasks = [checker.check_image(*car) for car in cars]
        await asyncio.gather(*tasks)


async def main():
    await run_parser()
    await download_image()

    #server_task = asyncio.create_task(run_server())
    bot_task = asyncio.create_task(run_bot())
    await asyncio.gather(bot_task)


if __name__ == "__main__":
    asyncio.run(main())