from aiogram.types import InlineKeyboardMarkup, CallbackQuery

from bot.common import BaseKeyboard
from bot.setup.text import Text
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
            return await Text(self).get_select_body_text()

        elif self.action == "set_body":
            return "Установите уровень сложности для кузова:"

        elif self.action == "start_parse":
            return "Sorry, not implemented"


    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await self.get_main_menu_button()
        ]
        return self._get_keyboard(keyboard)

    def row(self, text, **cd_kwargs):
        return [(text, self.make_cd(**cd_kwargs))]

    async def _get_action_buttons(self):

        match self.action:
            case "set_db":
                return await self.get_main_db_button()
            case "select_body":
                return await self.get_select_body_buttons()
            case _:
                return []

    async def get_main_db_button(self):
        return [
            self.row("ПЕРЕБРАТЬ ВСЕ ТИПЫ КУЗОВА 💿", action="set_body"),
            self.row("НАЗНАЧИТЬ СЛОЖНОСТЬ ОТДЕЛЬНО 🔧", action="select_body"),
            self.row("ЗАПУСК ПАРСЕРА 🔍️", action="start_parse"),
        ]

    async def get_select_body_buttons(self):
        if not self.id:
            items = await db.get_all_body()
            buttons = [
                [(body.body, self.make_cd(action="select_body", id=await db.get_body_id(body.body)))]
                for body in items
            ]
            buttons += self._back(action="set_db")
            return buttons

        elif not self.difficulty:
            buttons = [
                [(str(level), self.make_cd(difficulty=level)) for level in range(1, 6)],
                [(str(level), self.make_cd(difficulty=level)) for level in range(6, 11)],
            ]
            buttons += self._back(id=None)
            return buttons

        else:
            await db.put_difficulty_not_processed(self.id, self.difficulty)
            return [self.row("В НАСТРОЙКИ БАЗЫ ДАННЫХ ⚙", action="set_db", id=None, difficulty=None)]


    def _back(self, **kwargs):
        return [
            [("🔙 НАЗАД 🔙", self.make_cd(**kwargs))]
        ]
