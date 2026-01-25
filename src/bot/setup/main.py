from aiogram.types import InlineKeyboardMarkup, CallbackQuery

from bot.common import BaseKeyboard
from models import User
from db.ctrl import db


def parse_callback_data(callback: str):
    try:
        handler, data = callback.split(":")
        action, values = data.split("#")
        id, difficulty = values.split("*")
        print(f"act {action} id{id} diff{difficulty}")
        return action, id, difficulty

    except ValueError:
        return None, []


class SetupCallbackDataController(BaseKeyboard):
    action: str | None
    id: int | None
    difficulty: int | None

    def __init__(self, callback: CallbackQuery, user: User):
        super().__init__(user)
        parsed = parse_callback_data(callback.data)
        self.action, self.id, self.difficulty = parsed


    def make_cd(self, **kwargs):
        return (f"setup:{kwargs.get("action", self.action) or ""}#"
                f"{kwargs.get("id", self.id) or ""}*"
                f"{kwargs.get("difficulty", self.difficulty) or ""}")

    async def text(self) -> str | None:
        if self.action == "set_db":
            return "НАСТРОЙКИ БАЗЫ ДАННЫХ"

        elif self.action == "select_body":
            return ("Выберите тип кузова для выбора уровня сложности.\n\n"
                    "ВНИМАНИЕ!!! Сложность будет изменена ДЛЯ ВСЕХ АВТОМОБИЛЕЙ "
                    "с выбранным кузовом, кроме тех, которые назначены вручную.")

        elif self.action == "set_body":
            return "Установите уровень сложности для кузова:"

        elif self.action == "parse":
            return "Sorry, not implemented"



    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await self.get_main_menu_button()
        ]
        return self._get_keyboard(keyboard)

    async def _get_action_buttons(self):

        def row(text, **cd_kwargs):
            return [(text, self.make_cd(**cd_kwargs))]

        async def back(action, **kwargs):
            return [await self._back(action, **kwargs)]

        match self.action:

            case "set_db":
                return [
                    row("ПЕРЕБРАТЬ ВСЕ ТИПЫ 💿", action="set_body"),
                    row("НАЗНАЧИТЬ ОТДЕЛЬНО ", action="select_body"),
                    row("ЗАПУСК ПАРСЕРА 🔍️", action="parse"),
                ]

            case "select_body":
                items = await db.get_all_body()
                buttons = [
                    [(body.body, self.make_cd(id=await db.get_body_id(body.body )))]
                    for body in items
                ]
                buttons += await back("set_db")
                print(buttons)
                return buttons

            case _:
                return []

    # async def get_action_buttons(self):
    #     if self.action == "select_body":
    #         case "set_body":
    #             return await self.setup_difficulty()
    #         case "select_body":
    #             return await self.setup_difficulty()
    #         case _:
    #             return []

    async def setup_difficulty(self):
        buttons = self.get_difficulty_buttons(make_cd=self.make_cd)
        buttons += await self._back(id=None)
        return buttons

    async def _back(self, action: str = None, id: int = None, difficulty: int = None):
        return [
            ("🔙 НАЗАД 🔙", self.make_cd(action=action, id=id, difficulty=difficulty))
        ]
