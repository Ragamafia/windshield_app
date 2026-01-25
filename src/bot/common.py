from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class BaseKeyboard:

    def __init__(self, user):
        self.user = user

    @staticmethod
    async def get_main_menu_button():
        return [
            [("⤴ ГЛАВНОЕ МЕНЮ ⤴", "/start")]
        ]


    @staticmethod
    def _get_keyboard(colls: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=text, callback_data=callback) for text, callback in row]
                for row in colls
            ]
        )
