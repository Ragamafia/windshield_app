import asyncio

import uvicorn

from bot.bot import DetailerBot
from db.ctrl import db
from logger import logger


async def run_bot():
    logger.info(f'DetailerBot started')
    bot = DetailerBot()
    await bot.run()

async def run_server():
    logger.info(f'App started')
    config = uvicorn.Config("app.app:app", host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()


from db.temp_ctrl import temp_db
from db.old_ctrl import old_db


async def main():
    #await db.setup_db()

    # #await db.delete_user(1377785914)  # Admin
    # #await db.delete_user(8082484525)  # Admin

    # server_task = asyncio.create_task(run_server())

    #all_diff = await temp_db.get_difficulty()
    #await db.setup_db()
    #for i in all_diff:
        #await db.update_level(i.glass_id, i.difficulty)
    await old_db.setup_db()
    all_cars = await old_db.get_all_cars()
    print(f"Get all cars: {len(all_cars)}")
    await temp_db.setup_db()
    for i in all_cars:
        await temp_db.put_difficulty(i.glass_id, i.difficulty)

    bot_task = asyncio.create_task(run_bot())
    await asyncio.gather(bot_task)


if __name__ == "__main__":
    asyncio.run(main())
