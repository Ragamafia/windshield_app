import functools

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from bot.cars.handlers import register_car_handlers
from bot.partners.handlers import register_partners_handlers
from db.ctrl import db
from models import User
from config import cfg
from logger import logger


class DetailerBot(Bot):

    def __init__(self):
        props = DefaultBotProperties(parse_mode="HTML")
        super().__init__(cfg.bot_token, default=props)
        storage = MemoryStorage()
        self.router: Router = Router()
        self.dp: Dispatcher = Dispatcher(storage=storage)

    async def run(self):
        self.dp.include_router(self.router)
        register_car_handlers(self)
        register_partners_handlers(self)

        await self.set_my_commands([
            BotCommand(command='/start', description='Start bot 🟢')
        ])
        await self.dp.start_polling(self)

    def authorize(self, handler):
        @functools.wraps(handler)
        async def wrapper(callback: Message | CallbackQuery):
            msg = callback if isinstance(callback, Message) else callback

            if user := await db.get_user(msg.from_user.id):
                return await handler(callback, user)

            else:
                try:
                    qr_code_id = msg.text.split(" ")[1]
                    is_manager = True
                except IndexError:
                    is_manager = False
                user = callback.from_user
                user_dict = await db.create_user(user.id,
                                                 user.username,
                                                 user.first_name,
                                                 admin=user.id in cfg.admins,
                                                 is_manager=is_manager)

                logger.info(f'Create user: {user.first_name}, '
                            f'ID {user.id}. is_admin={user_dict["admin"]}. is_manager={user_dict["is_manager"]}')
                user = User(**user_dict)
                return await handler(callback, user)

        return wrapper
