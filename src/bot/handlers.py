from pathlib import Path

from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.ctrl import db
from config import cfg
from logger import logger


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
    brand: str | None
    model: str | None
    years: str | None
    level: str | None

    def __init__(self, callback: CallbackQuery):
        action, brand, model, years, level = parse_callback_data(callback.data)
        self.action = action
        self.brand = brand
        self.model = model
        self.years = years
        self.level = level

        self.year_start = self.years.split("-")[0]
        self.processed = False

    async def text(self) -> str:
        if self.action == "setup" and not self.brand and not self.model:
            if no_difficulty := await db.get_model_info():
                self.brand = no_difficulty["brand"]
                self.model = no_difficulty["model"]
                self.years = no_difficulty["groups"][0]["years"]
                self.year_start = self.years.split("-")[0]

                return await self.text()

            else:
                return "All done. Drink some beer, dude"

        elif self.action == "stat":
            logger.info(
                f"Request statistic. "
                f"Processed - {await db.count_level_true()}. "
                f"Left - {await db.count_level_false()}"
            )
            return (f"Обработано автомобилей - {await db.count_level_true()}\n"
                    f"Осталось - {await db.count_level_false()}")

        elif not self.brand:
            return f"Выберите бренд:"
        elif not self.model:
            return f"Выберите модель для {self.brand.capitalize()}:"
        elif not self.years:
            return f"Выберите года выпуска для {self.brand.capitalize()} {self.model.capitalize()}:"
        elif not self.level:
            gen = await db.get_gen(self.brand, self.model, self.year_start)
            return (
                f"Уровень сложности для\n"
                f"{self.brand.upper()} {self.model.upper()},\n "
                f"{gen} поколение, {self.years}"
            )
        else:
            self.gen = await db.get_gen(self.brand, self.model, self.year_start)
            self.saved_info = await db.update_level(self.brand, self.model, self.gen, self.level)

            self.show_level = self.level
            self.level = None
            self.brand = None
            self.model = None
            self.years = None

            self.processed = True
            return await self.text()

    def text_saved(self):
        lines = ["Сохранено ✅"]

        for key, values in self.saved_info.items():
            lines.append(f'{key.upper()}, {self.gen} поколение.')
            for v in values:
                lines.append(v)

        lines.append(f"Уровень сложности - {self.show_level}")
        return "\n".join(lines)

    async def keyboard(self) -> InlineKeyboardMarkup | None:
        if self.action == "setup" and not self.brand and not self.model:
            if no_difficulty := await db.get_model_info():
                self.brand = no_difficulty["brand"]
                self.model = no_difficulty["model"]
                self.years = no_difficulty["groups"][0]["years"]
                self.start = self.years.split("-")[0]

                return await self.keyboard()
            else:
                return

        elif self.action == "stat":
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

        return InlineKeyboardMarkup(inline_keyboard=[row_1, row_2])

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
        if all((self.brand, self.model, self.year_start, not self.level)):
            glass_id = await db.get_glass_id(self.brand, self.model, self.year_start)
            return Path(cfg.path_to_images / self.brand / self.model / glass_id / "img.jpg")


def register_main_handlers(bot):
    @bot.router.callback_query()
    async def universal_callback_handler(callback: CallbackQuery):
        data = CallBackData(callback)
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
    async def start_handler(message: Message):
        keyboard = CallBackData._get_keyboard([
            [
                ("ВЫБОР АВТО", "select#***"),
                ("ОПРОС БАЗЫ", "setup#***"),
            ], [
                ("СТАТИСТИКА", "stat#***"),
                ("ПАРСЕР", "parse"),
            ]
        ])
        await message.answer("ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)