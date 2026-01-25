from aiogram.types import InlineKeyboardMarkup, CallbackQuery

from bot.partners.text import Text
from bot.common import BaseKeyboard
from models import User
from db.ctrl import db


def parse_callback_data(callback: str):
    try:
        handler, data = callback.split(":")
        action, values = data.split("#")
        company, user_id = values.split("*")
        print(action, company, user_id)
        return action, company, user_id

    except ValueError:
        return None, []


class PartnerCallbackController(BaseKeyboard):
    action: str | None
    company: str | None
    user_id: int | None

    def __init__(self, callback: CallbackQuery, user: User):
        super().__init__(user)
        parsed = parse_callback_data(callback.data)
        self.action, self.company, self.user_id = parsed

    def make_cd(self, **kwargs):
        return (f"partners:{kwargs.get("action", self.action) or ""}#"
                f"{kwargs.get("company", self.company) or ""}*"
                f"{kwargs.get("user_id", self.user_id) or ""}")

    async def text(self) -> str | None:
        if self.action == "set_partners":
            return "НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ"
        elif self.action == "users":
            return "ВСЕ ПОЛЬЗОВАТЕЛИ:"
        elif self.action == "company_add_manager":
            return "В какую компанию добавить сотрудника?"
        elif self.action == "remove_company":
            return "ВЫ УВЕРЕНЫ?"
        elif self.action == "user":
            return await Text(self).get_user_info_text()
        elif self.action == "manager":
            return await Text(self).get_manager_info_text()
        elif self.action == "managers":
            return await Text(self).get_all_managers_text()
        elif self.action == "partner":
            return await Text(self).get_partner_info_text()
        elif self.action == "partners":
            return await Text(self).get_partners_text()
        elif self.action == "company_managers":
            return await Text(self).get_company_managers_text()
        elif self.action == "update":
            return await Text(self).pin_manager_text()
        elif self.action == "unpin_company":
            return await Text(self).unpin_manager_text()
        elif self.action == "confirm":
            return await Text(self).partner_delete()


    async def keyboard(self) -> InlineKeyboardMarkup | None:
        keyboard = [
            * await self._get_action_buttons(),
            * await self.get_main_menu_button()
        ]
        return self._get_keyboard(keyboard)

    def row(self, text, **kwargs):
        return [(text, self.make_cd(**kwargs))]

    async def _back(self, **kwargs):
        return [[("🔙 НАЗАД 🔙", self.make_cd(**kwargs))]]


    async def _get_action_buttons(self):

        match self.action:
            case "set_partners":
                return await self.handle_main_menu()
            case "partners":
                return await self.handle_partners()
            case "users":
                return await self.handle_users()
            case "managers":
                return await self.handle_managers()
            case "partner":
                return await self.handle_partner()
            case "company_managers":
                return await self.handle_company_managers()
            case "manager":
                return await self.handle_manager()
            case "user":
                return await self._back(action="users")
            case "company_add_manager":
                return await self.handle_company_add_manager()
            case "update":
                return await self._back(action="set_partners")
            case "remove_company":
                return await self.handle_yes_or_no()
            case "confirm":
                return [self.row("В НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ 👥", action="set_partners")]
            case "unpin_company":
                return await self._back(action="set_partners")
            case _:
                return []

    async def handle_main_menu(self):
        return [
            self.row("ДОБАВИТЬ НОВУЮ КОМПАНИЮ 🆕", action="add"),
            self.row("СПИСОК КОМПАНИЙ 🗂️", action="partners"),
            self.row("МЕНЕДЖЕРЫ 👔", action="managers"),
            self.row("ВСЕ ПОЛЬЗОВАТЕЛИ 🗄️", action="users"),
        ]

    async def handle_partners(self):
        partners = await db.get_partners()
        buttons = [
            self.row(p.name, action="partner", company=p.name)
            for p in partners
        ]
        buttons += await self._back(action="set_partners")
        return buttons

    async def handle_users(self):
        users = await db.get_users()
        buttons = [
            self.row(u.first_name, action="user", user_id=u.user_id)
            for u in users
        ]
        buttons += await self._back(action="set_partners")
        return buttons

    async def handle_managers(self):
        managers = await db.get_users()
        buttons = [
            self.row(m.first_name, action="manager", user_id=m.user_id)
            for m in managers if m.is_manager
        ]
        buttons += await self._back(action="set_partners")
        return buttons

    async def handle_partner(self):
        return [
            self.row("ИЗМЕНИТЬ СКИДКУ 💰", action="edit_discount", company=self.company),
            self.row("МЕНЕДЖЕРЫ 👔", action="company_managers", company=self.company),
            self.row("УДАЛИТЬ КОМПАНИЮ 🗑️", action="remove_company"),
            *(await self._back(action="partners")),
        ]

    async def handle_company_managers(self):
        partner = await db.get_partner(self.company)
        managers = await db.get_users_by_id(partner.partner_id)
        buttons = [
            self.row(m.first_name, action="manager", user_id=m.user_id)
            for m in managers
        ]
        buttons += await self._back(action="partner", company=self.company)
        return buttons

    async def handle_manager(self):
        manager = await db.get_user(self.user_id)
        base_action = "partner" if self.company else "managers"

        if manager.company_id:
            main_button = self.row("ОТВЯЗАТЬ ОТ КОМПАНИИ ➖", action="unpin_company",
                              user_id=self.user_id)
        else:
            main_button = self.row("ДОБАВИТЬ В КОМПАНИЮ ➕", action="company_add_manager")

        return [
            main_button,
            *(await self._back(action=base_action, company=self.company)),
        ]

    async def handle_company_add_manager(self):
        partners = await db.get_partners()
        buttons = [
            self.row(p.name, action="update", company=p.name)
            for p in partners
        ]
        buttons += await self._back(action="managers", company=self.company)
        return buttons

    async def handle_yes_or_no(self):
        return [
            self.row("ДА ✅", action="confirm", company=self.company),
            self.row("НЕТ ❌", action="set_partners"),
        ]
