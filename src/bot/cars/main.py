from pathlib import Path

from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.common import BaseKeyboard
from bot.cars.texts import Text
from models import User
from db.ctrl import db
from config import cfg


def parse_callback_data(callback: str):
    try:
        _, data = callback.split(":")
        action, values = data.split("#", 1)
        brand_start_letter, brand, model, years, letter_and_level = values.split("*") if values else []
        letter_and_level = letter_and_level.split("##")
        model_start_letter = letter_and_level[0] if letter_and_level[0] else ""
        level = letter_and_level[1]
        return action, brand_start_letter, brand, model, years, model_start_letter, level

    except ValueError:
        return None, []


class CarCallbackDataController(BaseKeyboard):
    action: str | None
    brand_start_letter: str | None
    model_start_letter: str | None
    brand: str | None
    model: str | None
    years: str | None
    level: str | None

    def __init__(self, callback: CallbackQuery, user: User):
        super().__init__(user)

        self.user = user
        self.action, self.brand_start_letter, self.brand, self.model, self.years, self.model_start_letter, self.level = parse_callback_data(callback.data)
        self.year_start = self.years.split("-")[0]

    async def post_init(self):
        if self.brand and self.model and self.years:
            self.car = await db.get_car(self.brand, self.model, self.year_start)
            if self.level:
                self.updated = await db.update_level(self.brand, self.model, self.car.gen, self.level)
                self.temp_level = self.level
                if self.action == "set":
                    self.level, self.brand_start_letter, self.brand, self.model, self.years = None, None, None, None, None

    def make_cd(self: "CallBackData", **kwargs) -> str:
        return (f"car:{kwargs.get("action", self.action) or ""}#"
                f"{kwargs.get("brand_start_letter", self.brand_start_letter) or ""}*"
                f"{kwargs.get("brand", self.brand) or ""}*"
                f"{kwargs.get("model", self.model) or ""}*"
                f"{kwargs.get("years", self.years) or ""}*"
                f"{kwargs.get("model_start_letter", self.model_start_letter) or ""}##"
                f"{kwargs.get("level", self.level) or ""}")

    async def text(self) -> str | None:
        if self.action == "set":
            return await Text(self).get_set_text()
        elif self.action == "car":
            return await Text(self).get_select_car_text()
        elif self.action == "stat":
            return await Text(self).get_stat_text()
        elif self.action == "info":
            return await Text(self).get_result_text()
        elif self.action == "parse":
            return await Text(self).get_parse_text()
        elif self.action == "edit":
            return await Text(self).get_edit_text()


    async def keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            *await self._get_action_buttons(),
            *await self.get_main_menu_button()
        ]
        return self._get_keyboard(keyboard)

    async def _get_action_buttons(self):
        match self.action:
            case "set":
                if no_difficulty := await db.get_model_info():
                    self.brand = no_difficulty["brand"]
                    self.model = no_difficulty["model"]
                    self.years = no_difficulty["groups"][0]["years"]
                    return await self.get_car_buttons()
            case "car":
                return await self.get_car_buttons()
            case "edit":
                return await self.get_car_buttons()
            case "info":
                if not self.user.admin:
                    return [
                        [("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", "car:contact#****##")]
                    ] + self.back(action="car")
                else:
                    return self.back(action="car")
            case _:
                return []

    async def get_car_buttons(self):
        if self.action == "car":
            if not self.brand_start_letter:
                return self.get_brand_alphabet()

            else:
                items = await self.get_items()
                if not self.brand:
                    return items + self.back(brand_start_letter=None)
                if not self.model:
                    if self.model_start_letter:
                        return items + self.back(model_start_letter=None)
                    else:
                        return items + self.back(brand=None)
                if not self.years:
                    return items + self.back(model=None)

        elif self.action in ("edit", "set"):
            if not self.level:
                return [
                    [(str(level), self.make_cd(level=level)) for level in range(1, 6)],
                    [(str(level), self.make_cd(level=level)) for level in range(6, 11)],
                ] + self.back(action="car")
            else:
                return self.back(action="car", level=None)

        elif self.action == "car" and self.brand and self.model and self.years:
            buttons = [[("ПОЛУЧИТЬ ИНФО ℹ️", self.make_cd(action="info"))]]
            if self.user.admin:
                buttons.append([("РЕДАКТИРОВАТЬ ⚙️", self.make_cd(action="edit"))])
            else:
                buttons.append([("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", "car:contact#****##")])
            return buttons + self.back(years=None)

        else:
            if self.model_start_letter:
                return self.back(model_start_letter=None)
            else:
                return self.back(brand_start_letter=None)

    async def get_items(self):
        if not self.brand:
            if brands := await db.get_brands(self.brand_start_letter):
                return [
                    [(b.brand.upper(), self.make_cd(brand=b.brand))]
                    for b in brands
                ]
            return []

        elif not self.model:
            available_models = await db.get_avialable_models(self.brand)
            if len(available_models) > cfg.MAX_PAGE_SIZE:
                if not self.model_start_letter:
                    return self.get_model_alphabet()
                else:
                    available_models = await db.get_avialable_models(self.brand, self.model_start_letter)

            result = [
                m for m in await db.get_models(self.brand)
                if m.model in available_models
            ]
            return [
                [(m.model.upper(), self.make_cd(model=m.model))]
                for m in result
            ]

        elif not self.years:
            car_gens = await db.get_gens(self.brand, self.model)
            items = [f"{g.year_start}-{g.year_end}" for g in car_gens]
            return [
                [(years, self.make_cd(years=years))]
                for years in items
            ]
        else:
            return []

    def get_brand_alphabet(self, prefix="car:car#", chunk=7):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        rows = [alphabet[i:i + chunk] for i in range(0, len(alphabet), chunk)]
        return [
            [(f"   {ch.upper()}   ", f"{prefix}{ch}****##") for ch in row]
            for row in rows
        ]

    def get_model_alphabet(self, prefix="car:car#", chunk=7):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        rows = [alphabet[i:i + chunk] for i in range(0, len(alphabet), chunk)]
        return [
            [(f"   {ch.upper()}   ", f"{prefix}{self.brand_start_letter}*{self.brand}***{ch}##") for ch in row]
            for row in rows
        ]

    def back(self, **kwargs):
        return [[("🔙 НАЗАД 🔙", self.make_cd(**kwargs))]]

    async def get_photo(self):
        if all((self.brand, self.model, self.year_start, not self.level)):
            car = await db.get_car(self.brand, self.model, self.year_start)
            return Path(cfg.path_to_images / self.brand / self.model / car.glass_id / "img.jpg")
