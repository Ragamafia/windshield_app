from pathlib import Path

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from utils import Calculate
from models import User
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
        self.user = user
        self.action, self.brand, self.model, self.years, self.level = parsed
        self.year_start = self.years.split("-")[0]
        self.finish = False

    async def saved_level(self):
        if self.level:
            self.gen = await db.get_gen(self.brand, self.model, self.year_start)
            self.saved_info = await db.update_level(self.brand, self.model, self.gen, self.level)
            self.show_level = self.level
            self.level, self.brand, self.model, self.years = None, None, None, None
            if self.action == "edit":
                self.action = None

    async def text(self) -> str | None:
        if self.action == "set" and not self.brand and not self.model:
            return await self.get_quest_text()
        elif self.action == "stat":
            return await self.get_stat_text()
        elif self.action == "car":
            return await self.get_car_text()
        elif self.action == "info":
            return await self.get_info_text()
        elif self.action == "parse":
            return await self.get_parse_text()
        elif self.action == "contact":
            return await self.get_contact_text()
        elif gen := await db.get_gen(self.brand, self.model, self.year_start):
            return (
                f"Установите уровень сложности\n"
                f"{self.brand.upper()} {self.model.upper()},\n"
                f"{gen} поколение, {self.years}"
            )
        else:
            lines = ["Сохранено ✅"]
            for key, values in self.saved_info.items():
                lines.append(f'{key.upper()}, {self.gen} поколение.')
                for v in values:
                    lines.append(v)
            lines.append(f"Уровень сложности - {self.show_level}")

            return "\n".join(lines)

    async def get_quest_text(self):
        if no_difficulty := await db.get_model_info():
            self.brand = no_difficulty["brand"]
            self.model = no_difficulty["model"]
            self.years = no_difficulty["groups"][0]["years"]
            self.year_start = self.years.split("-")[0]

            return await self.text()

        elif self.finish:
            return "All done. Drink some beer, dude"

    async def get_stat_text(self):
        logger.info(
            f"Request statistic. "
            f"Processed - {await db.count_level_true()}. "
            f"Left - {await db.count_level_false()}"
        )
        return (f"Обработано автомобилей - {await db.count_level_true()}\n"
                f"Осталось - {await db.count_level_false()}")

    async def get_car_text(self):
        if self.action == "car" and not self.brand:
            return f"Выберите бренд:"

        elif self.action == "car" and not self.model:
            return f"Выберите модель для {self.brand.capitalize()}:"

        elif self.action == "car" and not self.years:
            return f"Выберите года выпуска для {self.brand.capitalize()} {self.model.capitalize()}:"

        elif self.action == "car":
            gen = await db.get_gen(self.brand, self.model, self.year_start)
            return (
                f"{self.brand.upper()} {self.model.upper()}\n"
                f"{gen} поколение, {self.years}\n"
                f"Выберите действие"
            )

    async def get_info_text(self):
        id = await db.get_glass_id(self.brand, self.model, self.year_start)
        gen = await db.get_gen(self.brand, self.model, self.year_start)
        height, width = await Calculate()._get_size(id)
        return (
            f"{self.brand.upper()} {self.model.upper()},\n"
            f"{gen} поколение, {self.years}\n"
            f"Размер лобового стекла: \n"
            f"Высота - {height}\n"
            f"Ширина - {width}\n"
        )

    async def get_parse_text(self):
        return "Sorry, not implemented"

    async def get_contact_text(self):
        return "Sorry, not implemented"

    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await self._get_pagination_buttons(),
            * await self._get_go_back_buttons()
        ]
        return self._get_keyboard(keyboard)

    async def _get_action_buttons(self):
        match self.action:
            case "set" :
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

        elif self.action == "edit" or self.action == "set":
            return [
                [(str(level), make_cd(self, level=level)) for level in range(1, 6)],
                [(str(level), make_cd(self, level=level)) for level in range(6, 11)]
            ]
        else:
            if self.user.admin:
                return [
                    [("ПОЛУЧИТЬ ИНФО ℹ️", make_cd(self, action="info"))],
                    [("РЕДАКТИРОВАТЬ ⚙️", make_cd(self, action="edit"))]
            ]
            else:
                return [
                    [("ПОЛУЧИТЬ ИНФО ℹ️", make_cd(self, action="info"))],
                    [("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", make_cd(self, action="contact"))]
                ]

    async def _get_pagination_buttons(self):
        return []

    async def _get_go_back_buttons(self):
        return [[("ГЛАВНОЕ МЕНЮ 🔙", "/start")]]

    @staticmethod
    def _get_keyboard(colls: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=text, callback_data=callback) for text, callback in row]
                for row in colls
            ]
        )

    async def get_photo(self):
        if all((self.brand, self.model, self.year_start, not self.level)):
            glass_id = await db.get_glass_id(self.brand, self.model, self.year_start)
            return Path(cfg.path_to_images / self.brand / self.model / glass_id / "img.jpg")