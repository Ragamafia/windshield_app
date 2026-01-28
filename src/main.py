import asyncio

import uvicorn

from bot.bot import DetailerBot
from db.ctrl import db
from logger import logger
from config import cfg
from parser.car import CarParser
#from db.temp_ctrl import temp_db


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
        workers.append(CarParser(db))
    await workers[0].get_new_brands()
    await asyncio.gather(*[worker.run() for worker in workers])
    logger.success(f'Parse process complete. Total cars: {await db.count_cars()}.')

async def main():
    await db.setup_db()
    await run_parser(db)
    # #await db.delete_user(1377785914)  # Admin
    # #await db.delete_user(8082484525)  # Admin

    # server_task = asyncio.create_task(run_server())
    #await temp_db.setup_db()
    #all_diff = await temp_db.get_difficulty()
    #await db.setup_db()
    #for i in all_diff:
        #await db.update_level(i.glass_id, i.difficulty)

    bot_task = asyncio.create_task(run_bot())
    await asyncio.gather(bot_task)


if __name__ == "__main__":
    asyncio.run(main())
