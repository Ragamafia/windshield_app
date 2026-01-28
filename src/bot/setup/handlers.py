import asyncio

from aiogram import F
from aiogram.types import CallbackQuery

from parser.car import CarParser
from bot.setup.main import SetupCallbackController
from db.ctrl import db
from models import User
from logger import logger
from config import cfg


def register_setup_handlers(bot):
    @bot.router.callback_query(F.data.startswith("setup:"))
    @bot.authorize
    async def setup_callback_handler(callback: CallbackQuery, user: User):
        data = SetupCallbackController(callback, user)
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)

    @bot.router.callback_query(F.data.startswith("start_parse"))
    @bot.authorize
    async def start_parse_handler(callback: CallbackQuery, user: User):
        asyncio.create_task(run_parser(db))
        keyboard = [
            [("🔙 ВЕРНУТЬСЯ В НАСТРОЙКИ БАЗЫ 🔙", "setup:set_db#*")]
        ]
        keyboard = SetupCallbackController._get_keyboard(keyboard)
        await callback.message.answer("PARSE PROCESS... ⏱⏱⏱\n\n", reply_markup=keyboard)


async def run_parser(db):
    logger.info(f'Parse process...')
    workers = []
    for _ in range(cfg.WORKERS_COUNT):
        workers.append(CarParser(db))
    await workers[0].get_new_brands()
    await asyncio.gather(*[worker.run() for worker in workers])
    logger.success(f'Parse process complete. Total cars: {await db.count_cars()}.')
