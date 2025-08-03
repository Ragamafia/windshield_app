from pathlib import Path

from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.ctrl import db
from config import cfg


def parse_callback_data(callback: str):
    try:
        action, value = callback.split("#", 1)
        brand, model, year, data = value.split("*") if value else []
        return action, brand, model, year, data

    except ValueError:
        return None, []


class CallBackData:
    action: str
    brand: str
    model: str
    years: str
    data: str

    def __init__(self, callback: CallbackQuery):
        action, brand, model, years, data = parse_callback_data(callback.data)
        self.action = action
        self.brand = brand
        self.model = model
        self.years = years
        self.data = data

    async def get_path_to_image(self):
        self.start = self.years.split("-")[0]
        glass_id = await db.get_glass_id(self.brand, self.model, self.start)
        return Path(cfg.path_to_images / self.brand / self.model / glass_id / "img.jpg")

    async def text(self) -> str:
        if self.action == "setup" and not self.brand and not self.model:
            if no_difficulty := await db.get_model_info():
                self.brand = no_difficulty["brand"]
                self.model = no_difficulty["model"]
                return await self.text()

            else:
                return "All done. Drink some beer, dude"

        elif not self.brand:
            return f"Выберите бренд:"
        elif not self.model:
            return f"Выберите модель для {self.brand.capitalize()}:"
        elif not self.years:
            return f"Выберите года выпуска для {self.brand.capitalize()} {self.model.capitalize()}:"
        elif not self.data:
            gen = await db.get_gen(self.brand, self.model, self.start)
            return (
                f"Уровень сложности для\n"
                f"{self.brand.upper()} {self.model.upper()},\n "
                f"{gen} поколение, {self.years}"
            )

    async def keyboard(self) -> InlineKeyboardMarkup | None:
        if self.action == "setup" and not self.brand and not self.model:
            if no_difficulty := await db.get_model_info():
                self.brand = no_difficulty["brand"]
                self.model = no_difficulty["model"]
                return await self.keyboard()
            else:
                return

        elif not self.brand:
            brands = await db.get_brands()
            return self._get_keyboard(
                [[(brand.brand.upper(), f"{self.action}#{brand.brand}***")] for brand in brands]
            )

        elif not self.model:
            models = await db.get_models(self.brand)
            result = []
            for model in models:
                callback_value = f"{self.action}#{self.brand}*{model.model}**"
                result.append([(model.model.upper(), callback_value)])
            return self._get_keyboard(result)

        elif not self.years:
            car_gens = await db.get_gens(self.brand, self.model)
            result = []
            for gen in car_gens:
                years = f"{gen.year_start}-{gen.year_end}"
                callback_value = f"{self.action}#{self.brand}*{self.model}*{years}*"
                result.append([(years, callback_value)])
            return self._get_keyboard(result)

        elif not self.data:
            return self.level_buttons()

    def level_buttons(self):
        row_1 = [InlineKeyboardButton(text=str(level), callback_data=f"level_{level}") for level in range(1, 6)]
        row_2 = [InlineKeyboardButton(text=str(level), callback_data=f"level_{level}") for level in range(6, 11)]
        row_3 = [InlineKeyboardButton(text="NEXT >>>", callback_data="next")]
        return InlineKeyboardMarkup(inline_keyboard=[row_1, row_2, row_3])

    def _get_keyboard(self, colls: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=text, callback_data=callback)
            ]
            for rows in colls
            for text, callback in rows
        ])


def register_main_handlers(bot):
    @bot.router.callback_query()
    async def universal_callback_handler(callback: CallbackQuery):
        data = CallBackData(callback)
        try:
            if image_path := await data.get_path_to_image():
                await _send_photo(callback, image_path)
        except:
            ...
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)


    @bot.router.message(CommandStart())
    async def start_handler(message: Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Редактировать", callback_data="edit#***"),
                InlineKeyboardButton(text="Установить сложность", callback_data="setup#***")
            ]
        ])
        await message.answer("Выберите действие", reply_markup=keyboard)


    async def _send_photo(callback: CallbackQuery, image_path: Path):
        await bot.send_photo(
            callback.from_user.id,
            photo=FSInputFile(image_path),
        )

    # @bot.router.callback_query(lambda c: c.data and c.data.startswith('level_'))
    # async def process_level_callback(callback_query: CallbackQuery):
    #     level = callback_query.data.split('_')[1]
    #     gen = None
    #     for i in callback_query.message.caption.split():
    #         if i.isdigit():
    #             gen = int(i)
    #             break
    #
    #     await bot.send_message(callback_query.from_user.id, f"Выбран уровень сложности - {level}.")
    #     await db.update_info(gen, level)
