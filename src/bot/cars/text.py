from db.ctrl import db
from app.calc import Calculate
from utils import aprooved
from config import cfg
from logger import logger


class Text():

    def __init__(self, data):
        self.data = data

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
            if len(models) > cfg.max_brand_list:

                if not self.data.model_start_letter:
                    return f"Выберите букву для модели {self.data.brand.upper()}:"
                elif models := await db.get_avialable_models(self.data.brand, self.data.model_start_letter):
                    return f"Выберите модель для {self.data.brand.upper()}:"
                elif not models:
                    return f'У {self.data.brand.upper()} нет моделей на "{self.data.model_start_letter.capitalize()}" 🤷‍♂️'
            else:
                return f"Выберите модель для {self.data.brand.upper()}:"

        elif self.data.action == "car" and not self.data.years:
            return f"Выберите года выпуска для {self.data.brand.capitalize()} {self.data.model.capitalize()}:"

        elif self.data.action == "car" and not self.data.body:
            return (f"Выберите тип кузова для\n{self.data.brand.upper()} {self.data.model.upper()}\n"
                    f"{self.data.years} года")

        else:
            return (
                f"{self.data.brand.upper()} {self.data.model.upper()}\n"
                f"{self.data.car.gen} поколение, {self.data.years}\n"
                f"Выберите действие:"
            )

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
                    f"Уровень сложности - {self.data.updated.difficulty}")

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
        price_usa, price_korea = await Calculate(self.data.car.width, self.data.car.difficulty, discount).get_prices()
        film_usa, film_korea = await Calculate(self.data.car.width, self.data.car.difficulty, discount).get_only_film_prices()
        no_difficulty = (f"{cfg.default_setup}р. (default❗)")
        no_height = (f"{cfg.default_height} (default❗)")
        no_width = (f"{cfg.default_width} (default❗)")

        info = (
            f"<code>"
            f"{self.data.brand.upper()} {self.data.model.upper()},\n"
            f"{self.data.car.gen} поколение, {self.data.years}\n\n"
            f"Cтоимость бронирования\n"
            f"Плёнка США: {price_usa}р.\n"
            f"Пленка Корея: {price_korea}р.\n\n"
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
                f"Расход материала\n"
                f"Пленка USA: {film_usa}\n"
                f"Пленка KOREA: {film_korea}\n\n"
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
