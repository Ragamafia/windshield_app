import pytz

from aiogram.types import InlineKeyboardMarkup, CallbackQuery

from bot.common import BaseKeyboard
from models import User
from db.ctrl import db
from config import cfg


def parse_callback_data(callback: str):
    try:
        handler, data = callback.split(":")
        action, values = data.split("#")
        company, user_id = values.split("*")
        return action, company, user_id

    except ValueError:
        return None, []


class PartnerCallBackController(BaseKeyboard):
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
            return "ПОЛЬЗОВАТЕЛИ:"
        elif self.action == "company_add_manager":
            return "В какую компанию добавить сотрудника?"
        elif self.action == "remove":
            return "ВЫ УВЕРЕНЫ?"
        elif self.action == "user":
            return await self.get_user_info_text()
        elif self.action == "manager":
            return await self.get_manager_info_text()
        elif self.action == "managers":
            return await self.get_managers_text()
        elif self.action == "partner":
            return await self.get_partner_info_text()
        elif self.action == "partners":
            return await self.get_partners_text()
        elif self.action == "company_managers":
            return await self.get_company_managers_text()
        elif self.action == "update":
            return await self.pin_manager_text()
        elif self.action == "remove_company":
            return await self.unpin_manager_text()
        elif self.action == "remove_partner":
            return await self.partner_delete()

    async def get_managers_text(self):
        if managers := await db.get_managers():
            return "МЕНЕДЖЕРЫ:"
        else:
            return "Список менеджеров пуст 🤷‍♂️"

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
                f"Менеджер: {manager.first_name}\n"
                f"Компания: {company.name}\n"
                f"Дисконт: {company.discount}%\n\n"
                f"Выберите действие:"
            )
        else:
            return (
                f"Менеджер: {manager.first_name}\n"
                f"Компания не назначена.\n\n"
                f"Выберите действие:"
            )

    async def get_user_info_text(self):
        user = await db.get_user(self.user_id)
        if user.admin:
            status = "АДМИНИСТРАТОР"
        else:
            status = "МЕНЕДЖЕР" if user.is_manager else "ПОЛЬЗОВАТЕЛЬ"

        if company_ok := await db.get_partner_by_id(user.company_id):
            name = company_ok.name
        else:
            name = "Нет"
        discount = company_ok.discount if company_ok else "Общие условия - 0"
        tz = pytz.timezone(cfg.irkutsk_tz)
        create_at = user.created_at.astimezone(tz)
        return (
            f"<code>"
            f"Пользователь: {user.first_name}\n\n"
            f"ID: {user.user_id}\n"
            f"Username: {user.username}\n\n"
            f"Статус: {status}\n"
            f"Компания: {name}\n"
            f"Дисконт: {discount}%\n\n"
            f"Создан: {create_at.strftime("%d.%m.%Y %H:%M")}\n\n"
            f"</code>"
        )

    async def pin_manager_text(self):
        if partner := await db.get_partner(self.company):
            await db.update_user(self.user_id, partner.partner_id)
            return (
                f"Менеджер добавлен в компанию {partner.name}\n"
            )

    async def unpin_manager_text(self):
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
            * await self.get_main_menu_button()
        ]
        return self._get_keyboard(keyboard)

    async def _get_action_buttons(self):

        def row(text, **cd_kwargs):
            return [(text, self.make_cd(**cd_kwargs))]

        async def back(action, **kwargs):
            return [await self._back(action, **kwargs)]

        match self.action:

            case "set_partners":
                return [
                    row("ДОБАВИТЬ НОВУЮ КОМПАНИЮ 🆕", action="add"),
                    row("СПИСОК КОМПАНИЙ 🗂️", action="partners"),
                    row("МЕНЕДЖЕРЫ 👔", action="managers"),
                    row("ВСЕ ПОЛЬЗОВАТЕЛИ 🗄️", action="users"),
                ]

            case "partners":
                partners = await db.get_partners()
                buttons = [
                    row(p.name, action="partner", company=p.name)
                    for p in partners
                ]
                buttons += await back("set_partners")
                return buttons

            case "users":
                users = await db.get_users()
                buttons = [
                    row(u.first_name, action="user", user_id=u.user_id)
                    for u in users
                ]
                buttons += await back("set_partners")
                return buttons

            case "managers":
                managers = await db.get_users()
                buttons = [
                    row(m.first_name, action="manager", user_id=m.user_id)
                    for m in managers if m.is_manager
                ]
                buttons += await back("set_partners")
                return buttons

            case "partner":
                return [
                    row("ИЗМЕНИТЬ СКИДКУ 💰", action="edit_discount", company=self.company),
                    row("МЕНЕДЖЕРЫ 👔", action="company_managers", company=self.company),
                    row("УДАЛИТЬ КОМПАНИЮ 🗑️", action="remove"),
                    *(await back("partners")),
                ]

            case "company_managers":
                partner = await db.get_partner(self.company)
                managers = await db.get_users_by_id(partner.partner_id)

                buttons = [
                    row(m.first_name, action="manager", user_id=m.user_id)
                    for m in managers
                ]
                buttons += await back("partner", company=self.company)
                return buttons

            case "manager":
                manager = await db.get_user(self.user_id)
                base_action = "partner" if self.company else "managers"

                if manager.company_id:
                    main_button = row("ОТВЯЗАТЬ ОТ КОМПАНИИ ➖", action="remove_company",
                                      user_id=self.user_id)
                else:
                    main_button = row("ДОБАВИТЬ В КОМПАНИЮ ➕", action="company_add_manager")

                return [
                    main_button,
                    *(await back(base_action, company=self.company)),
                ]

            case "user":
                return [
                    *(await back("users")),
                ]

            case "company_add_manager":
                partners = await db.get_partners()
                buttons = [
                    row(p.name, action="update", company=p.name)
                    for p in partners
                ]
                buttons += await back("managers", company=self.company)
                return buttons

            case "update":
                return await back("set_partners")

            case "remove":
                return [
                    row("ДА ✅", action="remove_partner", company=self.company),
                    row("НЕТ ❌", action="set_partners"),
                ]

            case "remove_partner":
                return [
                    row("В НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ 👥", action="set_partners"),
                ]

            case "remove_company":
                return await back("set_partners")

            case _:
                return []

    async def _back(self, action: str, company=None):
        return [
            ("🔙 НАЗАД 🔙", self.make_cd(action=action, company=company))
        ]
