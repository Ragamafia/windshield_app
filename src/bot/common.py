from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from models import User
from db.ctrl import db
from logger import logger


class BaseController:

    def __init__(self, user: User):
        self.user = user

    async def get_stat_text(self):
        logger.info(
            f"Request statistic. User {self.user.first_name}. "
            f"Processed - {await db.count_processed_level(level=True)}. "
            f"Left - {await db.count_processed_level(level=False)}"
        )
        return (f"Обработано автомобилей - {await db.count_processed_level(level=True)}\n"
                f"Осталось - {await db.count_processed_level(level=False)}")

    async def get_parse_text(self):
        logger.info(f"User {self.user.first_name}. Start parse")
        return "Sorry, not implemented"


    @staticmethod
    async def _get_main_menu_buttons():
        return [[("⤴ ГЛАВНОЕ МЕНЮ ⤴", "/start")]]

    async def _back(self, action: str, company=None):
        return [
            ("🔙 НАЗАД 🔙", self.make_cd(action=action, company=company))
        ]

    @staticmethod
    def _get_keyboard(colls: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=text, callback_data=callback) for text, callback in row]
                for row in colls
            ]
        )
