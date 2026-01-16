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
        brand_letter, brand, model, years, letter_level_page = values.split("*") if values else []
        letter_and_level = letter_level_page.split("##")
        level_and_page = letter_and_level[1].split("&")
        model_letter = letter_and_level[0] if letter_and_level[0] else ""
        level = level_and_page[0] if level_and_page[0] else ""
        page = int(level_and_page[1]) if level_and_page[1] else 0
        return action, brand_letter, brand, model, years, model_letter, level, page

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
    page: int | None

    def __init__(self, callback: CallbackQuery, user: User):
        super().__init__(user)

        self.user = user
        self.action, self.brand_start_letter, self.brand, self.model, self.years, self.model_start_letter, self.level, self.page = parse_callback_data(
            callback.data)
        self.year_start = self.years.split("-")[0]

    async def post_init(self):
        if self.brand and self.model and self.years:
            self.car = await db.get_car(self.brand, self.model, self.year_start)
            if self.level:
                self.updated = await db.update_level(self.brand, self.model, self.car.gen, self.level)
                self.temp_level = self.level
                if self.action == "set":
                    self.level, self.brand_start_letter, self.brand, self.model, self.years, self.page = None, None, None, None, None, None

    def make_cd(self: "CallBackData", **kwargs) -> str:
        return (f"car:{kwargs.get("action", self.action) or ""}#"
                f"{kwargs.get("brand_start_letter", self.brand_start_letter) or ""}*"
                f"{kwargs.get("brand", self.brand) or ""}*"
                f"{kwargs.get("model", self.model) or ""}*"
                f"{kwargs.get("years", self.years) or ""}*"
                f"{kwargs.get("model_start_letter", self.model_start_letter) or ""}##"
                f"{kwargs.get("level", self.level) or ""}&"
                f"{kwargs.get('page', self.page) or ''}")

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
            *await self._get_pagination_buttons(),
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
                        [("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", "car:contact#****##&")]
                    ] + self.back(action="car")
                else:
                    return self.back(action="car")
            case _:
                return []

    async def get_car_buttons(self):
        if self.action == "car" and not self.brand_start_letter:
            return self.get_brand_alphabet()

        if items := await self.get_items():
            buttons = await self.get_page_items(items)
            if not self.brand:
                return buttons + self.back(brand_start_letter=None)
            if not self.model:
                if self.model_start_letter:
                    return buttons + self.back(model_start_letter=None)
                else:
                    return buttons + self.back(brand=None)
            if not self.years:
                return buttons + self.back(model=None)

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
                buttons.append([("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", "car:contact#****##&")])
            return buttons + self.back(years=None)

        else:
            if self.model_start_letter:
                return self.back(model_start_letter=None)
            else:
                return self.back(brand_start_letter=None)

    async def get_items(self):
        if not self.brand:
            brands = await db.get_brands(self.brand_start_letter)
            return [
                [(b.brand.upper(), self.make_cd(brand=b.brand))]
                for b in brands
            ]

        elif not self.model:
            available_models = await db.get_avialable_models(self.brand)
            if len(available_models) > cfg.max_models_list:
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

    async def _get_pagination_buttons(self):
        result = []
        if self.action == "car" and self.brand_start_letter:
            if items := await self.get_items():
                if len(items) > cfg.max_models_list:
                    pages = len(items) // cfg.max_models_list
                    if self.page > 0:
                        result.append(("<<<", self.make_cd(page=self.page - 1)))

                    for page in range(0, pages + 1):
                        name = f"[{page + 1}]" if page == self.page else f"{page + 1}"
                        result.append((name, self.make_cd(page=page)))

                    if pages != self.page:
                        result.append((">>>", self.make_cd(page=self.page + 1)))
            return [result]
        else:
            return []

    async def get_page_items(self, items):
        if len(items) > cfg.max_models_list:
            page = self.page if self.page else 0
            return items[page * cfg.max_models_list:(page + 1) * cfg.max_models_list]
        else:
            return items

    def get_brand_alphabet(self, prefix="car:car#", letters_in_row=7):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        rows = [alphabet[i:i + letters_in_row] for i in range(0, len(alphabet), letters_in_row)]
        return [
            [(f"   {ch.upper()}   ", f"{prefix}{ch}****##&") for ch in row]
            for row in rows
        ]

    def get_model_alphabet(self, prefix="car:car#", letters_in_row=7, digits_in_row=5):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        digits = [str(d) for d in range(10)]
        rows = [alphabet[i:i + letters_in_row] for i in range(0, len(alphabet), letters_in_row)]
        digit_rows = [digits[i:i + digits_in_row] for i in range(0, len(digits), digits_in_row)]
        all_rows = rows + digit_rows
        return [
            [(f"   {ch.upper()}   ", f"{prefix}{self.brand_start_letter}*{self.brand}***{ch}##&") for ch in row]
            for row in all_rows
        ]

    def back(self, **kwargs):
        return [[("🔙 НАЗАД 🔙", self.make_cd(**kwargs))]]

    async def get_photo(self):
        if all((self.brand, self.model, self.year_start, not self.level)):
            car = await db.get_car(self.brand, self.model, self.year_start)
            return Path(cfg.path_to_images / self.brand / self.model / car.glass_id / "img.jpg")
