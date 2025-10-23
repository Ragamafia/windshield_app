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


class PartnerCallBackController:
    action: str | None
    company: str | None
    user_id: int | None

    def __init__(self, callback: CallbackQuery, user: User):
        parsed = parse_callback_data(callback.data)
        self.action, self.company, self.user_id = parsed

    def make_cd(self, **kwargs):
        return (f"partners:{kwargs.get("action", self.action) or ""}#"
                f"{kwargs.get("company", self.company) or ""}*"
                f"{kwargs.get("user_id", self.user_id) or ""}")

    async def text(self) -> str | None:
        if self.action == "set_partners":
            return "НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ"
        elif self.action == "managers":
            return "МЕНЕДЖЕРЫ:"
        elif self.action == "company_add_manager":
            return "В какую компанию добавить сотрудника?"
        elif self.action == "remove":
            return "ВЫ УВЕРЕНЫ?"
        elif self.action == "partners":
            return await self.get_partners_text()
        elif self.action == "partner":
            return await self.get_partner_info_text()
        elif self.action == "manager":
            return await self.get_manager_info_text()
        elif self.action == "company_managers":
            return await self.get_company_managers_text()
        elif self.action == "update":
            return await self.update()
        elif self.action == "remove_company":
            return await self.remove_company()
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
        buttons = []
        match self.action:
            case "set_partners":
                return [
                    [("ДОБАВИТЬ НОВУЮ КОМПАНИЮ 🆕", self.make_cd(action="add"))],
                    [("СПИСОК КОМПАНИЙ 🗂️", self.make_cd(action="partners"))],
                    [("ВСЕ МЕНЕДЖЕРЫ 👔", self.make_cd(action="managers"))]
                ]

            case "partners":
                if partners := await db.get_partners():
                    for partner in partners:
                        buttons.append(
                            [(partner.name, self.make_cd(action="partner", company=partner.name))]
                        )
                buttons.append(await self._back("set_partners"))
                return buttons

            case "managers":
                managers = await db.get_users()
                for manager in managers:
                    buttons.append(
                        [(manager.username, self.make_cd(action="manager", user_id=manager.user_id))]
                    )
                buttons.append(await self._back("set_partners"))
                return buttons

            case "partner":
                buttons = [
                [("ИЗМЕНИТЬ СКИДКУ 💰", self.make_cd(action="edit_discount", company=self.company))],
                [("МЕНЕДЖЕРЫ 👔", self.make_cd(action="company_managers", company=self.company))],
                [("УДАЛИТЬ КОМПАНИЮ 🗑️", self.make_cd(action="remove"))],
                await self._back("partners")
                ]
                return buttons

            case "company_managers":
                if partner := await db.get_partner(self.company):
                    if managers := await db.get_users_by_id(partner.partner_id):
                        for manager in managers:
                            buttons.append(
                                [(manager.username, self.make_cd(action="manager", user_id=manager.user_id))]
                            )
                    buttons.append(await self._back("partner", company=self.company))
                    return buttons

            case "manager":
                action = "partner" if self.company else "managers"
                manager = await db.get_user(self.user_id)
                if manager.company_id:
                    buttons.append(
                        [("ОТВЯЗАТЬ ОТ КОМПАНИИ ➖", self.make_cd(action="remove_company", user_id=self.user_id))]
                    )
                else:
                    buttons.append(
                        [("ДОБАВИТЬ В КОМПАНИЮ ➕", self.make_cd(action="company_add_manager"))]
                    )
                buttons.append(await self._back(action, company=self.company if self.company else None))
                return buttons

            case "company_add_manager":
                if partners := await db.get_partners():
                    for partner in partners:
                        buttons.append(
                            [(partner.name, self.make_cd(action="update", company=partner.name))]
                        )
                buttons.append(await self._back("managers", company=self.company))
                return buttons

            case ("update"):
                buttons.append(await self._back("set_partners"))
                return buttons

            case "remove":
                return [
                    [("ДА ✅", self.make_cd(action="remove_partner", company=self.company))],
                    [("НЕТ ❌", self.make_cd(action="set_partners"))]
                ]
            case "remove_partner":
                return [
                    [("В НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ 👥", self.make_cd(action="set_partners"))]
                ]

            case "remove_company":
                buttons.append(await self._back("set_partners"))
                return buttons

            case _:
                return []

    async def _back(self, action: str, company=None):
        return [
            ("🔙 НАЗАД 🔙", self.make_cd(action=action, company=company))
        ]
