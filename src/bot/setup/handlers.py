from aiogram import F
from aiogram.types import CallbackQuery

from bot.setup.main import SetupCallbackDataController
from models import User


def register_setup_handlers(bot):
    @bot.router.callback_query(F.data.startswith("setup:"))
    @bot.authorize
    async def partners_callback_handler(callback: CallbackQuery, user: User):
        data = SetupCallbackDataController(callback, user)
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)
