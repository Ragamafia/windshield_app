from pathlib import Path

from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.ctrl import db
from config import cfg


def parse_callback_data(callback: str):
    try:
        action, value = callback.split("#", 1)
        brand, model, years, level = value.split("*") if value else []
        return action, brand, model, years, level

    except ValueError:
        return None, []

def make_cd(cd: "CallBackData", **kwargs):
    return (f"{kwargs.get("action", cd.action) or ""}#"
            f"{kwargs.get("brand", cd.brand) or ""}*"
            f"{kwargs.get("model", cd.model) or ""}*"
            f"{kwargs.get("years", cd.years) or ""}*"
            f"{kwargs.get("level", cd.level) or ""}")


class CallBackData:
    action: str
    brand: str
    model: str
    years: str
    level: str

    def __init__(self, callback: CallbackQuery):
        action, brand, model, years, level = parse_callback_data(callback.data)
        self.action = action
        self.brand = brand
        self.model = model
        self.years = years
        self.level = level
        self.start = self.years.split("-")[0]

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
        elif not self.level:
            gen = await db.get_gen(self.brand, self.model, self.start)
            return (
                f"Уровень сложности для\n"
                f"{self.brand.upper()} {self.model.upper()},\n "
                f"{gen} поколение, {self.years}"
            )
        else:
            return (f"Сохранено ✅\n"
                    f"Уровень сложности - {self.level}.")

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
                [[(brand.brand.upper(), make_cd(self, brand=brand.brand))] for brand in brands]
            )

        elif not self.model:
            models = await db.get_models(self.brand)
            result = []
            for model in models:
                callback_value = make_cd(self, model=model.model)
                result.append([(model.model.upper(), callback_value)])
            return self._get_keyboard(result)

        elif not self.years:
            car_gens = await db.get_gens(self.brand, self.model)
            result = []
            for gen in car_gens:
                years = f"{gen.year_start}-{gen.year_end}"
                callback_value = make_cd(self, years=years)
                result.append([(years, callback_value)])
            return self._get_keyboard(result)

        elif not self.level:
            return self.level_buttons()

    def level_buttons(self):
        row_1 = [
            InlineKeyboardButton(
                text=str(level),
                callback_data=make_cd(self, level=level)) for level in range(1, 6)
        ]
        row_2 = [
            InlineKeyboardButton(
                text=str(level),
                callback_data=make_cd(self, level=level)) for level in range(6, 11)
        ]
        row_3 = [
            InlineKeyboardButton(text="NEXT >>>", callback_data="next")
        ]
        return InlineKeyboardMarkup(inline_keyboard=[row_1, row_2, row_3])

    @staticmethod
    def _get_keyboard(colls: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=text, callback_data=callback)
            ]
            for rows in colls
            for text, callback in rows
        ])

    async def get_photo(self):
        if all((self.brand, self.model, self.start)):
            glass_id = await db.get_glass_id(self.brand, self.model, self.start)
            return Path(cfg.path_to_images / self.brand / self.model / glass_id / "img.jpg")


def register_main_handlers(bot):
    @bot.router.callback_query()
    async def universal_callback_handler(callback: CallbackQuery):
        data = CallBackData(callback)
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


    @bot.router.message(CommandStart())
    async def start_handler(message: Message):
        keyboard = CallBackData._get_keyboard([
            [
                ("ВЫБОР АВТО", "select#***"),
                ("ОПРОС БАЗЫ", "setup#***"),
            ], [
                ("СТАТИСТИКА", "stat"),
                ("ПАРСЕР", "parse"),
            ]
        ])
        await message.answer("ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)