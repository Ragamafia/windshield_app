from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.cars.main import CarCallbackController
from models import User
from config import cfg


def register_car_handlers(bot):

    @bot.router.callback_query(F.data.startswith("/start"))
    @bot.router.message(CommandStart())
    @bot.authorize
    async def start_handler(message: Message | CallbackQuery, user: User):
        if user.admin:
            keyboard = [
                [("ВЫБОР АВТО 🚘", "car:car#*****##&")],
                [("НАСТРОЙКИ БАЗЫ ⚙️", "setup:set_db#*")],
                [("НАСТРОЙКИ ПАРТНЁРОВ 👥", "partners:set_partners#*")]
            ]
        else:
            keyboard = [
                [("ВЫБОР АВТО 🚘", "car:car#*****##&")],
                [("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", "car:contact")]
            ]
        keyboard = CarCallbackController._get_keyboard(keyboard)
        msg = message if isinstance(message, Message) else message.message
        await msg.answer("ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)


    @bot.router.callback_query(F.data.startswith("car:contact"))
    @bot.authorize
    async def contact_handler(callback: CallbackQuery, user: User):
        await bot.send_message(user.user_id,
                               f"Чтобы связаться перейдите по ссылке: {cfg.admin_url}")
        await callback.answer()


    @bot.router.callback_query(F.data.startswith("car:"))
    @bot.authorize
    async def car_callback_handler(callback: CallbackQuery, user: User):
        data = CarCallbackController(callback, user)
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
