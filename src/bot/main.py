from pathlib import Path

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery

from db.models import User
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
    action: str | None
    brand: str | None
    model: str | None
    years: str | None
    level: str | None

    def __init__(self, callback: CallbackQuery, user: User):
        parsed = parse_callback_data(callback.data)

        self.action, self.brand, self.model, self.years, self.level = parsed
        self.year_start = self.years.split("-")[0]
        self.processed = False
        self.finish = False
        self.user = user

    async def post_init(self):
        if self.action == "edit" and self.level:
            self.gen = await db.get_gen(self.brand, self.model, self.year_start)
            self.saved_info = await db.update_level(self.brand, self.model, self.gen, self.level)

            self.show_level = self.level
            self.level = None
            self.brand = None
            self.model = None
            self.years = None

            self.processed = True

    async def text(self) -> str | None:
        if self.action == "set" and not self.brand and not self.model:
            if no_difficulty := await db.get_model_info():
                self.brand = no_difficulty["brand"]
                self.model = no_difficulty["model"]
                self.years = no_difficulty["groups"][0]["years"]
                self.year_start = self.years.split("-")[0]

                return await self.text()

            elif self.finish:
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

        elif self.action == "car":
            gen = await db.get_gen(self.brand, self.model, self.year_start)
            return (
                f"{self.brand.upper()} {self.model.upper()}\n"
                f"{gen} поколение, {self.years}\n"
                f"Выберите действие"
            )

        else:
            gen = await db.get_gen(self.brand, self.model, self.year_start)
            return (
                f"Выберите уровень сложности\n"
                f"{self.brand.upper()} {self.model.upper()},\n "
                f"{gen} поколение, {self.years}"
            )

    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await self._get_pagination_buttons(),
            * await self._get_go_back_buttons()
        ]
        return self._get_keyboard(keyboard)

    async def _get_action_buttons(self):
        match self.action:
            case "set":
                if no_difficulty := await db.get_model_info():
                    self.brand = no_difficulty["brand"]
                    self.model = no_difficulty["model"]
                    self.years = no_difficulty["groups"][0]["years"]
                    self.year_start = self.years.split("-")[0]
                    return await self.get_car_buttons()

            case "car":
                return await self.get_car_buttons()
            case "edit":
                return await self.get_car_buttons()

            case _:
                return []

    async def get_car_buttons(self):
        if not self.brand:
            brands = await db.get_brands()
            return [[(b.brand.upper(), make_cd(self, brand=b.brand))] for b in brands]

        elif not self.model:
            models = await db.get_models(self.brand)
            return [[(m.model.upper(), make_cd(self, model=m.model))] for m in models]

        elif not self.years:
            car_gens = await db.get_gens(self.brand, self.model)
            return [[(f"{g.year_start}-{g.year_end}",
                      make_cd(self, years=f"{g.year_start}-{g.year_end}"))] for g in car_gens]

        elif self.action == "edit" or self.action == "set" and self.user.admin:
            return [
                [(str(level), make_cd(self, level=level)) for level in range(1, 6)],
                [(str(level), make_cd(self, level=level)) for level in range(6, 11)]
            ]
        else:
            if self.user.admin:
                return [
                    [("ПОЛУЧИТЬ ИНФО", make_cd(self, action="info"))],
                    [("РЕДАКТИРОВАТЬ", make_cd(self, action="edit"))]
            ]
            else:
                return [
                    [("ПОЛУЧИТЬ ИНФО", make_cd(self, action="info"))],
                    [("СВЯЗАТЬСЯ С МАСТЕРОМ", make_cd(self, action="contact"))]
                ]
            return []

    async def _get_pagination_buttons(self):
        return []

    async def _get_go_back_buttons(self):
        return [[("ГЛАВНОЕ МЕНЮ", "/start")]]


    def text_saved(self):
        lines = ["Сохранено ✅"]

        for key, values in self.saved_info.items():
            lines.append(f'{key.upper()}, {self.gen} поколение.')
            for v in values:
                lines.append(v)

        lines.append(f"Уровень сложности - {self.show_level}")
        return "\n".join(lines)

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