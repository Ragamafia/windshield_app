from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.main import CallBackData
from db.ctrl import db
from models import User
from config import cfg


def register_main_handlers(bot):
    @bot.router.callback_query(F.data.startswith("/start"))
    @bot.router.message(CommandStart())
    @bot.authorize
    async def start_handler(message: Message | CallbackQuery, user: User):
        if user.admin:
            keyboard = [
                [
                    ("ВЫБОР АВТО 🚘", "car#***##"),
                    ("ОПРОС БАЗЫ 💿", "set#***##"),
                ], [
                    ("СТАТИСТИКА 📝", "stat#***##"),
                    ("ПАРСЕР 🔍", "parse#***##"),
                ], [
                    ("ДОБАВИТЬ ПАРТНЁРА", "partner#***##")
                ], [
                    ("ПОЛУЧИТЬ СПИСОК ПАРТНЕРОВ", "partners#***##")
                ]
            ]
        else:
            keyboard = [
                [
                    ("ВЫБОР АВТО 🚘", "car#***##"),
                ], [
                    ("СВЯЗАТЬСЯ С НАМИ 📱", "contact#***##"),
                ]
            ]
        keyboard = CallBackData._get_keyboard(keyboard)
        msg = message if isinstance(message, Message) else message.message
        await msg.answer("ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)


    @bot.router.callback_query(F.data.startswith("contact"))
    @bot.authorize
    async def contact_handler(callback: CallbackQuery, user: User):
        await bot.send_message(user.user_id,
                               f"Чтобы связаться, перейдите по ссылке: {cfg.admin_url}")
        await callback.answer()


    @bot.router.message()
    @bot.authorize
    async def get_partner_handler(callback: CallbackQuery, user: User):
        await db.put_partner(callback.text)
        await bot.send_message(user.user_id, f"Добавлен новый партнер: \n{callback.text}")


    @bot.router.callback_query()
    @bot.authorize
    async def universal_callback_handler(callback: CallbackQuery, user: User):
        data = CallBackData(callback, user)
        await data.saved_level()
        text = await data.text()
        keyboard = await data.keyboard()
        if photo := await data.get_photo():
            await callback.message.answer_photo(
                photo=FSInputFile(photo),
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(text, reply_markup=keyboard)
