from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.main import CallBackData
from db.models import User


def register_main_handlers(bot):
    @bot.router.callback_query()
    @bot.authorize
    async def universal_callback_handler(callback: CallbackQuery, user: User):
        data = CallBackData(callback, user)
        await data.post_init()
        text = await data.text()
        keyboard = await data.keyboard()
        if photo := await data.get_photo():
            if data.processed == True:
                await callback.message.answer(data.text_saved())

            await callback.message.answer_photo(
                photo=FSInputFile(photo),
                caption=text,
                reply_markup=keyboard
            )
        else:
            if data.processed == True:
                await callback.message.answer(data.text_saved())
            await callback.message.answer(text, reply_markup=keyboard)


    @bot.router.message(CommandStart())
    @bot.authorize
    async def start_handler(message: Message, user: User):
        if user.admin:
            keyboard = [
                [
                    ("ВЫБОР АВТО", "car#***"),
                    ("ОПРОС БАЗЫ", "set#***"),
                ], [
                    ("СТАТИСТИКА", "stat#***"),
                    ("ПАРСЕР", "parse#***"),
                ]
            ]
        else:
            keyboard = [
            [
                ("ВЫБОР АВТО", "car#***"),
            ], [
                ("СВЯЗАТЬСЯ С НАМИ", "contact#***"),
            ]
        ]
        keyboard = CallBackData._get_keyboard(keyboard)
        await message.answer("ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)