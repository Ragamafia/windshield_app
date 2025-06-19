import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from handlers import register_main_handlers
from config import cfg


class DetailerBot(Bot):

    def __init__(self):
        props = DefaultBotProperties(parse_mode="HTML")
        super().__init__(cfg.bot_token, default=props)

        self.router: Router = Router()
        self.dispatcher: Dispatcher = Dispatcher()

        self.dispatcher.include_router(self.router)
        register_main_handlers(self)

    def run(self):
        asyncio.run(self.serve())

    async def serve(self):
        await self.set_my_commands([
            BotCommand(command='/start', description='Start bot')
        ])
        await self.dispatcher.start_polling(self)


if __name__ == '__main__':
    bot = DetailerBot()
    bot.run()