from pathlib import Path

from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.common import BaseController
from app.calc import Calculate
from models import User
from utils import check_discount
from db.ctrl import db
from config import cfg
from logger import logger


def parse_callback_data(callback: str):
    try:
        _, data = callback.split(":")
        action, values = data.split("#", 1)
        letter, brand, model, years, page_and_level = values.split("*") if values else []
        page_and_level = page_and_level.split("##")
        page = int(page_and_level[0]) if page_and_level[0] else 0
        level = page_and_level[1]
        return action, letter, brand, model, years, page, level

    except ValueError:
        return None, []


class CarCallbackDataController(BaseController):
    action: str | None
    letter: str | None
    brand: str | None
    model: str | None
    years: str | None
    page: int | None
    level: str | None

    def __init__(self, callback: CallbackQuery, user: User):
        print(callback.data)
        super().__init__(user)
        self.user = user
        self.action, self.letter, self.brand, self.model, self.years, self.page, self.level = parse_callback_data(callback.data)
        self.year_start = self.years.split("-")[0]

    async def post_init(self):
        if self.brand and self.model and self.years:
            self.car = await db.get_car(self.brand, self.model, self.year_start)
            if self.level:
                self.updated = await db.update_level(self.brand, self.model, self.car.gen, self.level)
                self.temp_level = self.level
                if self.action == "set":
                    self.level, self.letter, self.brand, self.model, self.years = None, None, None, None, None

    def make_cd(self: "CallBackData", **kwargs):
        return (f"car:{kwargs.get("action", self.action) or ""}#"
                f"{kwargs.get("letter", self.letter) or ""}*"
                f"{kwargs.get("brand", self.brand) or ""}*"
                f"{kwargs.get("model", self.model) or ""}*"
                f"{kwargs.get("years", self.years) or ""}*"
                f"{kwargs.get("page", self.page) or ""}##"
                f"{kwargs.get("level", self.level) or ""}")

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
        if self.action == "car" and not self.letter:
            return f"Выберите букву:"
        elif self.action == "car" and not self.brand:
            if brands := await db.get_brands(self.letter):
                return f"Выберите бренд:"
            else:
                return f'В базе нет брендов на букву "{self.letter.upper()}" 🤷‍♂️'
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

    async def get_glass_info_text(self):
        discount = await check_discount(self.user)
        if discount or str(discount) == "0":
            price_usa, price_korea = await Calculate(self.car.width, self.car.difficulty).get_prices()
            film_usa, film_korea = await Calculate(self.car.width, self.car.difficulty).get_only_film_prices()
            no_difficulty = (f"{cfg.default_setup}р. (default❗)")
            no_height = (f"{cfg.default_height} (default❗)")
            no_width = (f"{cfg.default_width} (default❗)")

            info = (
                f"<code>"
                f"{self.brand.upper()} {self.model.upper()},\n"
                f"{self.car.gen} поколение, {self.years}\n\n"
                f"Cтоимость бронирования стекла\n"
                f"Плёнка США: {price_usa - (price_usa * discount / 100)}р.\n"
                f"Пленка Корея: - {price_korea - (price_korea * discount / 100)}р.\n\n"
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
                    f"Стоимость потраченной плёнки\n"
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
            logger.info(f"User {self.user.first_name}. Request car info {self.brand.upper()} {self.model.upper()} {self.years}")
            return info

        else:
            return (
                f"Пожалуйста, дождитесь авторизации ⏱\n"
                f"Если ваш вопрос срочный, свяжитесь с администратором ⬇️\n"
                f"{cfg.admin_url}"
            )


    async def keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            * await self._get_action_buttons(),
            * await self._get_pagination_buttons(),
            * await self.get_main_menu_button()
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
                        [("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", self.make_cd(action="contact"))]
                    ] + self.back(action="car")
                else:
                    return self.back(action="car")
            case _:
                return []

    async def get_car_buttons(self):

        if self.action == "car" and not self.letter:
            return self.get_alphabet_keyboard()

        elif items := await self.get_items():
            buttons = await self.get_page_items(items)
            if self.action == "car":
                if not self.brand:
                    return buttons + self.back(letter=None)
                if not self.model:
                    return buttons + self.back(brand=None)
                if not self.years:
                    return buttons + self.back(model=None)

            return buttons

        elif self.action in ("edit", "set"):
            if not self.level:
                return [
                    [(str(level), self.make_cd(level=level)) for level in range(1, 6)],
                    [(str(level), self.make_cd(level=level)) for level in range(6, 11)],
                ] + self.back(action="car")
            else:
                return self.back(action="car")

        elif self.action == "car" and self.brand and self.model and self.years:
            buttons = [
                [("ПОЛУЧИТЬ ИНФО ℹ️", self.make_cd(action="info"))],
            ]
            if self.user.admin:
                buttons.append([("РЕДАКТИРОВАТЬ ⚙️", self.make_cd(action="edit"))])
            else:
                buttons.append([("СВЯЗАТЬСЯ С МАСТЕРОМ 📱", self.make_cd(action="contact"))])

            return buttons + self.back(years=None)

        else:
            return self.back(letter=None)

    async def _get_pagination_buttons(self):
        result = []
        if self.action == "car":
            if items := await self.get_items():
                if len(items) > cfg.MAX_PAGE_SIZE:
                    pages = len(items) // cfg.MAX_PAGE_SIZE
                    if int(self.page) > 0:
                        result.append(("⏪", self.make_cd(page=self.page - 1)))

                    for page in range(1, pages + 1):
                        name = f"[{page + 1}]" if page == self.page else f"{page + 1}"
                        result.append((name, self.make_cd(page=page)))

                    if pages != self.page:
                        result.append(("⏩", self.make_cd(page=self.page + 1)))
            return [result]
        else:
            return []

    async def get_items(self):
        if self.action == "car" and not self.letter:
            return []

        elif not self.brand:
            if brands := await db.get_brands(self.letter):
                return [
                    [(b.brand.upper(), self.make_cd(brand=b.brand, page=0))]
                    for b in brands
                ]
            return []

        elif not self.model:
            available_models = await db.get_avialable_models(self.brand)
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

    async def get_page_items(self, items):
        if len(items) > cfg.MAX_PAGE_SIZE:
            page = self.page if self.page else 0
            return items[page * cfg.MAX_PAGE_SIZE: (page + 1) * cfg.MAX_PAGE_SIZE]
        else:
            return items

    def get_alphabet_keyboard(self, prefix="car:car#", chunk=7):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        rows = [alphabet[i:i + chunk] for i in range(0, len(alphabet), chunk)]
        return [
            [(f"      {ch.upper()}", f"{prefix}{ch}****##") for ch in row]
            for row in rows
        ]

    def back(self, **kwargs):
        return [[("🔙 НАЗАД 🔙", self.make_cd(**kwargs))]]

    async def get_photo(self):
        if all((self.brand, self.model, self.year_start, not self.level)):
            car = await db.get_car(self.brand, self.model, self.year_start)
            return Path(cfg.path_to_images / self.brand / self.model / car.glass_id / "img.jpg")
