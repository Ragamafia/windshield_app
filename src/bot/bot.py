from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from src.bot.handlers import register_main_handlers
from config import cfg


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
            BotCommand(command='/start', description='Start bot')
        ])
        await self.dp.start_polling(self)
