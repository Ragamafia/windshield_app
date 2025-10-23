from pathlib import Path

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from app.calc import Calculate
from db.ctrl import db
from models import User
from config import cfg
from logger import logger


def parse_callback_data(callback: str):
    try:
        handler, data = callback.split(":")
        action, values = data.split("#", 1)
        brand, model, years, page_and_level = values.split("*") if values else []
        page_and_level = page_and_level.split("##")
        paginate_page = int(page_and_level[0]) if page_and_level[0] else 0
        level = page_and_level[1]
        return action, brand, model, years, paginate_page, level

    except ValueError:
        return None, []

def make_cd(cd: "CallBackData", **kwargs):
    return (f"car:{kwargs.get("action", cd.action) or ""}#"
            f"{kwargs.get("brand", cd.brand) or ""}*"
            f"{kwargs.get("model", cd.model) or ""}*"
            f"{kwargs.get("years", cd.years) or ""}*"
            f"{kwargs.get("page", cd.page) or ""}##"
            f"{kwargs.get("level", cd.level) or ""}")

class BaseCallBackDataController:
    action: str | None
    brand: str | None
    model: str | None
    years: str | None
    page: int | None
    level: str | None

    def __init__(self, callback: CallbackQuery, user: User):
        self.user = user
        self.action, self.brand, self.model, self.years, self.page, self.level = parse_callback_data(callback.data)
        self.year_start = self.years.split("-")[0]

    async def post_init(self):
        if self.brand and self.model and self.years:
            self.car = await db.get_car(self.brand, self.model, self.year_start)
            if self.level:
                self.updated = await db.update_level(self.brand, self.model, self.car.gen, self.level)
                self.temp_level = self.level
                if self.action == "set":
                    self.level, self.brand, self.model, self.years = None, None, None, None

    async def text(self) -> str | None:
        if self.action == "set":
            return await self.get_set_text()
        elif self.action == "car":
            return await self.get_car_text()
        elif self.action == "stat":
            return await self.get_stat_text()
        elif self.action == "info":
            return await self.get_glass_info_text()
        elif self.action == "parse":
            return await self.get_parse_text()
        elif self.action == "edit":
            return await self.edited_text()

    async def get_set_text(self):
        if not self.brand and not self.model:
            if no_difficulty := await db.get_model_info():
                self.brand = no_difficulty["brand"]
                self.model = no_difficulty["model"]
                self.years = no_difficulty["groups"][0]["years"]
                self.year_start = self.years.split("-")[0]
                return await self.text()
            else:
                return "All done. Drink some beer, dude)"
        else:
            return await self.edited_text()

    async def edited_text(self):
        if not self.level:
            return (
                f"Установите уровень сложности\n"
                f"{self.brand.upper()} {self.model.upper()},\n"
                f"Года выпуска: {self.years}"
            )
        else:
            return ("Сохранено ✅\n"
                    f"{self.updated.model.upper()}, {self.updated.gen} поколение.\n"
                    f"{self.updated.year_start}-{self.updated.year_end}\n"
                    f"Уровень сложности - {self.temp_level}")

    async def get_car_text(self):
        if self.action == "car" and not self.brand:
            return f"Выберите бренд:"
        elif self.action == "car" and not self.model:
            return f"Выберите модель для {self.brand.capitalize()}:"
        elif self.action == "car" and not self.years:
            return f"Выберите года выпуска для {self.brand.capitalize()} {self.model.capitalize()}:"
        else:
            return (
                f"{self.brand.upper()} {self.model.upper()}\n"
                f"{self.car.gen} поколение, {self.years}\n"
                f"Выберите действие:"
            )

    async def get_stat_text(self):
        logger.info(
            f"Request statistic. User {self.user.username}. "
            f"Processed - {await db.count_processed_level(level=True)}. "
            f"Left - {await db.count_processed_level(level=False)}"
        )
        return (f"Обработано автомобилей - {await db.count_processed_level(level=True)}\n"
                f"Осталось - {await db.count_processed_level(level=False)}")

    async def get_glass_info_text(self):
        price_usa, price_korea = await Calculate(self.car.width, self.car.difficulty).get_prices()
        film_usa, film_korea = await Calculate(self.car.width, self.car.difficulty).get_only_film_prices()
        no_difficulty = (f"{cfg.default_setup}р. (default❗)")
        no_height = (f"{cfg.default_height} (default❗)")
        no_width = (f"{cfg.default_width} (default❗)")

        info = (
            f"<code>"
            f"{self.brand.upper()} {self.model.upper()},\n"
            f"{self.car.gen} поколение, {self.years}\n\n"
            f"Цена бронирования стекла\n"
            f"Плёнка США: {price_usa}р.\n"
            f"Пленка Корея: - {price_korea}р.\n\n"
            f"</code>"
        )
        for_user = (
            f"Для получения точной информации и записи на оклейку обратитесь пожалуйста к мастеру ⬇"
        )
        for_admin = (
                f"<code>"
                f"Размеры стекла\n"
                f"Высота: {self.car.height if self.car.height else no_height}\n"
                f"Ширина: {self.car.width if self.car.width else no_width}\n\n"
                f"Стоимость плёнки\n"
                f"USA: {film_usa}\n"
                f"KOREA: {film_korea}\n\n"
                f"Уровень сложности: {self.car.difficulty}\n"
                f"Стоимость работы - {cfg.setup.get(self.car.difficulty) if self.car.difficulty else no_difficulty}\n\n"
                f"</code>"
        )

        if self.user.admin:
            info += for_admin
        else:
            info += for_user
        logger.info(f"User {self.user.username}. Request car info {self.brand.upper()} {self.model.upper()} {self.years}")
        return info

    async def get_parse_text(self):
        logger.info(f"User {self.user.username}. Start parse")
        return "Sorry, not implemented"


    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await self._get_pagination_buttons(),
            * await self._get_main_menu_buttons()
        ]
        return self._get_keyboard(keyboard)

    async def _get_action_buttons(self):
        match self.action:
            case "set" :
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
                        [("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", make_cd(self, action="contact"))]
                    ]
                else:
                    return []
            case _:
                return []

    async def get_items(self):
        if not self.brand:
            brands = await db.get_brands()
            return [[(b.brand.upper(), make_cd(self, brand=b.brand, page=0))] for b in brands]

        elif not self.model:
            models = await db.get_models(self.brand)
            return [[(m.model.upper(), make_cd(self, model=m.model))] for m in models]

        elif not self.years:
            car_gens = await db.get_gens(self.brand, self.model)
            items = [f"{g.year_start}-{g.year_end}" for g in car_gens]
            return [[(g, make_cd(self, years=g))] for g in items]

    async def get_page_items(self, items):
        if len(items) > cfg.MAX_PAGE_SIZE:
            page = self.page if self.page else 0
            return items[page * cfg.MAX_PAGE_SIZE: (page + 1) * cfg.MAX_PAGE_SIZE]
        else:
            return items

    async def get_car_buttons(self):
        if items := await self.get_items():
            return await self.get_page_items(items)

        elif self.action == "edit" or self.action == "set":
            if not self.level:
                return [
                    [(str(level), make_cd(self, level=level)) for level in range(1, 6)],
                    [(str(level), make_cd(self, level=level)) for level in range(6, 11)]
                ]
            else:
                return []
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
        result = []
        if self.action == "car":
            if items := await self.get_items():
                if len(items) > cfg.MAX_PAGE_SIZE:
                    pages = len(items) // cfg.MAX_PAGE_SIZE
                    if int(self.page) > 0:
                        result.append(("⏪", make_cd(self, page=self.page - 1)))

                    for page in range(1, pages + 1):
                        name = f"[{page + 1}]" if page == self.page else f"{page + 1}"
                        result.append((name, make_cd(self, page=page)))

                    if pages != self.page:
                        result.append(("⏩", make_cd(self, page=self.page + 1)))
            return [result]
        else:
            return []

    @staticmethod
    async def _get_main_menu_buttons():
        return [[("⤴ ГЛАВНОЕ МЕНЮ ⤴", "/start")]]

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
            car = await db.get_car(self.brand, self.model, self.year_start)
            return Path(cfg.path_to_images / self.brand / self.model / car.glass_id / "img.jpg")
