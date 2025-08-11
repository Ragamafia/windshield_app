import functools

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, Message, CallbackQuery

from src.bot.handlers import register_main_handlers
from src.db.ctrl import db
from config import cfg
from logger import logger


class DetailerBot(Bot):

    def __init__(self):
        props = DefaultBotProperties(parse_mode="HTML")
        super().__init__(cfg.bot_token, default=props)

        self.router: Router = Router()
        self.dp: Dispatcher = Dispatcher()
        self.dp.include_router(self.router)
        register_main_handlers(self)

    async def run(self):
        await self.set_my_commands([
            BotCommand(command='/start', description='Start bot 🟢')
        ])
        await self.dp.start_polling(self)


    def authorize(self, handler):
        @functools.wraps(handler)
        async def wrapper(callback: Message | CallbackQuery):
            print(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
            if user := await db.get_user(callback.from_user.id):
                return await handler(callback, user)
            else:
                if callback.from_user.id in cfg.admins:
                    await db.create_admin(callback.from_user)
                    logger.info(f'Create user: {callback.from_user.first_name}. Status ADMIN')
                else:
                    await db.create_user(callback.from_user)
                    logger.info(f'Create user: {callback.from_user.first_name}')

                return await handler(callback, user)

        return wrapper
