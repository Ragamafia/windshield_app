from aiogram.types import InlineKeyboardMarkup, CallbackQuery

from bot.main import BaseCallBackDataController
from db.ctrl import db
from models import User


def parse_callback_data(callback: str):
    try:
        action, values = callback.split("#")
        partner, discount = values.split("*")
        discount = int(discount) if discount else 0
        return action, partner, discount

    except ValueError:
        return None, []

def make_cd(cd: "CallBackData", **kwargs):
    return (f"{kwargs.get("action", cd.action) or ""}#"
            f"{kwargs.get("partner", cd.partner) or ""}*"
            f"{kwargs.get("discount", cd.discount) or ""}")


class PartnerCallBackController:
    action: str | None
    partner: str | None
    discount: int | None

    def __init__(self, callback: CallbackQuery, user: User):
        print(callback.data)
        parsed = parse_callback_data(callback.data)
        self.action, self.partner, self.discount = parsed

    async def text(self) -> str | None:
        if self.action == "set_partners":
            return "МЕНЮ НАСТРОЕК"
        elif self.action == "partners":
            return "Список партнёров:"
        elif self.action == "partner":
            return await self.get_partner_info_text()
        elif self.action == "remove":
            return "ВЫ УВЕРЕНЫ?"
        elif self.action == "remove_partner":
            return await self.get_partner_delete_text()

    async def get_partner_info_text(self):
        partner = await db.get_partner(self.partner)
        return (
            f"INFO\n"
            f"Партнёр: {partner.name}\n"
            f"Текущая скидка: {partner.discount}%\n"
        )

    async def get_partner_delete_text(self):
        await db.delete_partner(self.partner)
        return "Партнёр удалён."


    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await BaseCallBackDataController._get_main_menu_buttons()
        ]
        return BaseCallBackDataController._get_keyboard(keyboard)

    async def _get_action_buttons(self):
        match self.action:
            case "set_partners":
                return [
                    [("ДОБАВИТЬ НОВОГО ПАРТНЁРА ➕", make_cd(self, action="add"))],
                    [("ПОЛУЧИТЬ СПИСОК ПАРТНЕРОВ 🗂️", make_cd(self, action="partners"))]
                ]
            case "partners":
                partners = await db.get_partners()
                return [
                    [(name.name, make_cd(self, action="partner", partner=name.name))] for name in partners
                ]
            case "partner":
                return [
                    [("РЕДАКТИРОВАТЬ 💰", make_cd(self, action="edit_discount", partner=self.partner))],
                    [("УДАЛИТЬ ПАРТНЁРА 🗑️", make_cd(self, action="remove"))]
                ]
            case "remove":
                return [
                    [("ДА ✅", make_cd(self, action="remove_partner", partner=self.partner))],
                    [("НЕТ ❌", make_cd(self, action="settings"))]
                ]
            case _:
                return []
