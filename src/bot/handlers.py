from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.main import BaseCallBackDataController
from models import User


def register_main_handlers(bot):
    @bot.router.callback_query(F.data.startswith("/start"))
    @bot.router.message(CommandStart())
    @bot.authorize
    async def start_handler(message: Message | CallbackQuery, user: User):
        if user.admin:
            keyboard = [
                [
                    ("ВЫБОР АВТО 🚘", "car:car#***##"),
                    ("ОПРОС БАЗЫ 💿", "car:set#***##"),
                ], [
                    ("СТАТИСТИКА 📝", "car:stat#***##"),
                    ("ПАРСЕР 🔍", "car:parse#***##"),
                ], [
                    ("НАСТРОЙКИ ПАРТНЁРОВ 🔧", "partners:set_partners#")
                ]
            ]
        else:
            keyboard = [
                [
                    ("ВЫБОР АВТО 🚘", "car:car#***##"),
                ], [
                    ("СВЯЗАТЬСЯ С НАМИ 📱", "car:contact#***##"),
                ]
            ]
        keyboard = BaseCallBackDataController._get_keyboard(keyboard)
        msg = message if isinstance(message, Message) else message.message
        await msg.answer("ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)


    @bot.router.callback_query(F.data.startswith("car:"))
    @bot.authorize
    async def car_callback_handler(callback: CallbackQuery, user: User):
        data = BaseCallBackDataController(callback, user)
        await data.post_init()
        text = await data.text()
        keyboard = await data.keyboard()
        if photo := await data.get_photo():
            await callback.message.answer_photo(
                photo=FSInputFile(photo),
                caption=text,
                reply_markup=keyboard
            )
        else:
            (await callback.message.answer(text, reply_markup=keyboard))
