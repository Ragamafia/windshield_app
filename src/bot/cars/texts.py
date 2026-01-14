from db.ctrl import db
from app.calc import Calculate
from utils import aprooved
from config import cfg
from logger import logger


class Text():

    def __init__(self, data):
        self.data = data

    async def get_set_text(self):
        if not self.data.brand and not self.data.model:
            if no_difficulty := await db.get_model_info():
                self.data.brand = no_difficulty["brand"]
                self.data.model = no_difficulty["model"]
                self.data.years = no_difficulty["groups"][0]["years"]
                self.data.year_start = self.data.years.split("-")[0]
                return await self.data.text()
            else:
                return "All done. Drink some beer, dude)"
        else:
            return await self.get_edit_text()

    async def get_edit_text(self):
        if not self.data.level:
            return (
                f"Установите уровень сложности\n"
                f"{self.data.brand.upper()} {self.data.model.upper()},\n"
                f"Года выпуска: {self.data.years}"
            )
        else:
            return ("Сохранено ✅\n"
                    f"{self.data.updated.model.upper()}, {self.data.updated.gen} поколение.\n"
                    f"{self.data.updated.year_start}-{self.data.updated.year_end}\n"
                    f"Уровень сложности - {self.data.temp_level}")

    async def get_select_car_text(self):
        if self.data.action == "car" and not self.data.brand_start_letter:
            return "Выберите букву:"
        elif self.data.action == "car" and not self.data.brand:
            if brands := await db.get_brands(self.data.brand_start_letter):
                return "Выберите бренд:"
            else:
                return f'В базе нет брендов на букву "{self.data.brand_start_letter.upper()}" 🤷‍♂️'

        elif self.data.action == "car" and not self.data.model:
            models = await db.get_avialable_models(self.data.brand)
            if len(models) > cfg.MAX_PAGE_SIZE:
                if not self.data.model_start_letter:
                    return f"Выберите букву для модели {self.data.brand.upper()}:"
                elif models := await db.get_avialable_models(self.data.brand, self.data.model_start_letter):
                    return f"Выберите модель для {self.data.brand.upper()}:"
                elif not models:
                    return f'У {self.data.brand.upper()} нет моделей на букву "{self.data.model_start_letter.capitalize()}" 🤷‍♂️'
            else:
                return f"Выберите модель для {self.data.brand.upper()}:"

        elif self.data.action == "car" and not self.data.years:
            return f"Выберите года выпуска для {self.data.brand.capitalize()} {self.data.model.capitalize()}:"
        else:
            return (
                f"{self.data.brand.upper()} {self.data.model.upper()}\n"
                f"{self.data.car.gen} поколение, {self.data.years}\n"
                f"Выберите действие:"
            )

    async def get_result_text(self):
        user = await db.get_user(self.data.user.user_id)
        if user.is_manager:
            if company := await aprooved(user):
                return await self.get_price_text(company.discount)
            else:
                return (
                    f"Пожалуйста, дождитесь авторизации ⏱\n"
                    f"Если ваш вопрос срочный, свяжитесь с администратором ⬇️\n"
                )
        else:
            return await self.get_price_text()

    async def get_price_text(self, discount=0):
        price_usa, price_korea = await Calculate(self.data.car.width, self.data.car.difficulty).get_prices()
        film_usa, film_korea = await Calculate(self.data.car.width, self.data.car.difficulty).get_only_film_prices()
        no_difficulty = (f"{cfg.default_setup}р. (default❗)")
        no_height = (f"{cfg.default_height} (default❗)")
        no_width = (f"{cfg.default_width} (default❗)")

        info = (
            f"<code>"
            f"{self.data.brand.upper()} {self.data.model.upper()},\n"
            f"{self.data.car.gen} поколение, {self.data.years}\n\n"
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
                f"Высота: {self.data.car.height if self.data.car.height else no_height}\n"
                f"Ширина: {self.data.car.width if self.data.car.width else no_width}\n\n"
                f"Стоимость потраченной плёнки\n"
                f"USA: {film_usa}\n"
                f"KOREA: {film_korea}\n\n"
                f"Уровень сложности: {self.data.car.difficulty}\n"
                f"Стоимость работы - {cfg.setup.get(self.data.car.difficulty) if self.data.car.difficulty else no_difficulty}\n\n"
                f"</code>"
        )

        if self.data.user.admin:
            info += for_admin
        else:
            info += for_user

        logger.info(f"User {self.data.user.first_name}. Request car info {self.data.brand.upper()} {self.data.model.upper()} {self.data.years}")
        return info

    async def get_stat_text(self):
        logger.info(
            f"Request statistic. User {self.data.user.first_name}. "
            f"Processed - {await db.count_processed_level(level=True)}. "
            f"Left - {await db.count_processed_level(level=False)}"
        )
        return (f"Обработано автомобилей - {await db.count_processed_level(level=True)}\n"
                f"Осталось - {await db.count_processed_level(level=False)}")

    async def get_parse_text(self):
        logger.info(f"User {self.data.user.first_name}. Start parse")
        return "Sorry, not implemented"
