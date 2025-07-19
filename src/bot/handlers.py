from pathlib import Path

from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.ctrl import db
from config import cfg
from logger import logger


def register_main_handlers(bot):
    @bot.router.message(Command(commands=['start']))
    async def start_command(message: Message):
        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[
                [KeyboardButton(text="NEXT >>>")],
                [
                    KeyboardButton(text="Получить инфо"),
                    KeyboardButton(text="Редактировать")
                ]
            ])
        await message.answer('Чтобы приступить к установке уровней сложности нажмите NEXT >>>', reply_markup=keyboard)

    def level_buttons():
        row_1 = [InlineKeyboardButton(text=str(level), callback_data=f"level_{level}") for level in range(1, 6)]
        row_2 = [InlineKeyboardButton(text=str(level), callback_data=f"level_{level}") for level in range(6, 11)]
        return InlineKeyboardMarkup(inline_keyboard=[row_1, row_2])


    @bot.router.message(lambda message: message.text == "NEXT >>>")
    async def handle_level(message: Message):
        if car := await db.get_model_info():
            level_none = next(group for group in car["groups"] if group.get("level") is None)

            image_path = Path(cfg.path_to_images / car.get("brand") / car.get("model") / level_none.get("ids")[0] / "img.jpg")

            await message.answer_photo(
                photo=FSInputFile(image_path),
                caption=f"Уровень сложности для\n"
                        f"{car.get("brand").upper()} {car.get("model").upper()}, "
                        f"{level_none.get("gen")} поколение, {level_none.get("years")}",
                reply_markup=level_buttons()
            )

    @bot.router.callback_query(lambda c: c.data and c.data.startswith('level_'))
    async def process_level_callback(callback_query: CallbackQuery):
        level = callback_query.data.split('_')[1]
        gen = None
        for i in callback_query.message.caption.split():
            if i.isdigit():
                gen = int(i)
                break

        await bot.send_message(callback_query.from_user.id, f"Выбран уровень сложности - {level}.")
        await db.update_info(gen, level)

    @bot.router.message(lambda message: message.text == "Получить инфо")
    async def handle_info(message: Message):
        logger.warning(f"Press INFO")