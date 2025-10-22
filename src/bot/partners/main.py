from aiogram.types import InlineKeyboardMarkup, CallbackQuery

from bot.main import BaseCallBackDataController
from models import User
from db.ctrl import db


def parse_callback_data(callback: str):
    try:
        handler, data = callback.split(":")
        action, values = data.split("#")
        company, user_id = values.split("*")
        return action, company, user_id

    except ValueError:
        return None, []

def make_cd(cd: "CallBackData", **kwargs):
    return (f"partners:{kwargs.get("action", cd.action) or ""}#"
            f"{kwargs.get("company", cd.company) or ""}*"
            f"{kwargs.get("user_id", cd.user_id) or ""}")


class PartnerCallBackController:
    action: str | None
    company: str | None
    user_id: int | None

    def __init__(self, callback: CallbackQuery, user: User):
        parsed = parse_callback_data(callback.data)
        self.action, self.company, self.user_id = parsed
        self.user = user

    async def text(self) -> str | None:
        if self.action == "set_partners":
            return "НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ"
        elif self.action == "partners":
            return await self.get_partners_text()
        elif self.action == "partner":
            return await self.get_partner_info_text()
        elif self.action == "managers":
            return "МЕНЕДЖЕРЫ:"
        elif self.action == "manager":
            return await self.get_manager_info_text()
        elif self.action == "company_managers":
            return await self.get_company_managers_text()
        elif self.action == "company_add_manager":
            return "В какую компанию добавить сотрудника?"
        elif self.action == "update":
            return await self.update()
        elif self.action == "remove_company":
            return await self.remove_company()
        elif self.action == "remove":
            return "ВЫ УВЕРЕНЫ?"
        elif self.action == "remove_partner":
            return await self.partner_delete()

    async def get_partners_text(self):
        if partners := await db.get_partners():
            return "ПАРТНЕРЫ:"
        else:
            return "Список партнеров пуст 🤷‍♂️"

    async def get_partner_info_text(self):
        partner = await db.get_partner(self.company)
        return (
            f'Партнёр: "{partner.name}"\n'
            f"Текущая скидка: {partner.discount}%\n\n"
            f"Выберите действие:"
        )

    async def get_company_managers_text(self):
        if partner := await db.get_partner(self.company):
            if managers := await db.get_users_by_id(partner.partner_id):
                return "МЕНЕДЖЕРЫ:"
            else:
                return "Список менеджеров пуст 🤷‍♂️"

    async def get_manager_info_text(self):
        manager = await db.get_user(self.user_id)
        if manager.company_id:
            company = await db.get_partner_by_id(manager.company_id)
            return (
                f"Менеджер: {manager.username}\n"
                f"Компания: {company.name}\n"
                f"Дисконт: {company.discount}%\n\n"
                f"Выберите действие:"
            )
        else:
            return (
                f"Менеджер: {manager.username}\n"
                f"Компания не назначена.\n\n"
                f"Выберите действие:"
            )

    async def update(self):
        if partner := await db.get_partner(self.company):
            await db.update_user(self.user_id, partner.partner_id)
            return (
                f"Менеджер добавлен в компанию {partner.name}\n"
            )

    async def remove_company(self):
            await db.update_user(self.user_id, None)
            return "Менеджер отвязан"

    async def partner_delete(self):
        partner = await db.get_partner(self.company)
        if managers := await db.get_users_by_id(partner.partner_id):
            for manager in managers:
                await db.update_user(manager.user_id, None)
        await db.delete_partner(self.company)
        return "Менеджеры отвязаны. Партнёр удалён."

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
                    [("ДОБАВИТЬ НОВУЮ КОМПАНИЮ 🆕", make_cd(self, action="add"))],
                    [("СПИСОК КОМПАНИЙ 🗂️", make_cd(self, action="partners"))],
                    [("ВСЕ МЕНЕДЖЕРЫ 👔", make_cd(self, action="managers"))]
                ]

            case "partners":
                if partners := await db.get_partners():
                    return [
                        [(partner.name, make_cd(self, action="partner", company=partner.name))] for partner in partners
                    ]
                else:
                    return [("🔙 НАЗАД 🔙", make_cd(self, action="set_partners"))]

            case "managers":
                managers = await db.get_users()
                return [
                    [(manager.username, make_cd(self, action="manager", user_id=manager.user_id))] for manager in
                    managers
                ]

            case "partner":
                return [
                    [("ИЗМЕНИТЬ СКИДКУ 💰", make_cd(self, action="edit_discount", company=self.company))],
                    [("МЕНЕДЖЕРЫ 👔", make_cd(self, action="company_managers", company=self.company))],
                    [("УДАЛИТЬ КОМПАНИЮ 🗑️", make_cd(self, action="remove"))],
                    [("🔙 НАЗАД 🔙", make_cd(self, action="set_partners"))]
                ]

            case "company_managers":
                if partner := await db.get_partner(self.company):
                    if managers := await db.get_users_by_id(partner.partner_id):
                        return [
                            [(manager.username, make_cd(self, action="manager", user_id=manager.user_id))] for manager in managers
                        ]
                    else:
                        return [
                            [("🔙 НАЗАД 🔙", make_cd(self, action="partner", company=self.company))]
                        ]
                else:
                    return [
                        [("🔙 НАЗАД 🔙", make_cd(self, action="partner", company=self.company))]
                    ]

            case "manager":
                manager = await db.get_user(self.user_id)
                if manager.company_id:
                    return [
                        [("ОТВЯЗАТЬ ОТ КОМПАНИИ ", make_cd(self, action="remove_company", user_id=self.user_id))],
                        [("🔙 НАЗАД 🔙", make_cd(self, action="set_partners"))]
                    ]
                else:
                    return [
                        [("ДОБАВИТЬ В КОМПАНИЮ ", make_cd(self, action="company_add_manager"))],
                        [("🔙 НАЗАД 🔙", make_cd(self, action="managers"))]
                    ]

            case "company_add_manager":
                if partners := await db.get_partners():
                    return [
                        [(partner.name, make_cd(self, action="update", company=partner.name, user_id=self.user_id))] for partner in partners
                    ]
                else:
                    return [("🔙 НАЗАД 🔙", make_cd(self, action="managers", company=self.company))]

            case ("update"):
                return [
                    [("🔙 НАЗАД 🔙", make_cd(self, action="set_partners"))]
                ]

            case "remove":
                return [
                    [("ДА ✅", make_cd(self, action="remove_partner", company=self.company))],
                    [("НЕТ ❌", make_cd(self, action="set_partners"))]
                ]

            case "remove_company":
                    return [
                        [("🔙 НАЗАД 🔙", make_cd(self, action="set_partners"))]
                    ]

            case _:
                return []
