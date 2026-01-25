import pytz

from db.ctrl import db
from config import cfg


class Text():

    def __init__(self, data):
        self.data = data

    async def get_all_managers_text(self):
        if managers := await db.get_managers():
            return "ВСЕ МЕНЕДЖЕРЫ:"
        else:
            return "Общий список менеджеров пуст 🤷‍♂️"

    async def get_partners_text(self):
        if partners := await db.get_partners():
            return "ПАРТНЕРЫ:"
        else:
            return "Список партнеров пуст 🤷‍♂️"

    async def get_partner_info_text(self):
        partner = await db.get_partner(self.data.company)
        return (
            f'Партнёр: "{partner.name}"\n'
            f"Текущая скидка: {partner.discount}%\n\n"
            f"Выберите действие:"
        )

    async def get_company_managers_text(self):
        if partner := await db.get_partner(self.data.company):
            if managers := await db.get_users_by_id(partner.partner_id):
                return f"МЕНЕДЖЕРЫ ПАРТНЕРА {partner.name}:"
            else:
                return f"Список менеджеров {partner.name.upper()} пуст 🤷‍♂️"

    async def get_manager_info_text(self):
        manager = await db.get_user(self.data.user_id)
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
        user = await db.get_user(self.data.user_id)
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
        if partner := await db.get_partner(self.data.company):
            await db.update_user(self.data.user_id, partner.partner_id)
            return (
                f"Менеджер добавлен в компанию {partner.name}\n"
            )

    async def unpin_manager_text(self):
        await db.update_user(self.data.user_id, None)
        return "Менеджер отвязан"

    async def partner_delete(self):
        partner = await db.get_partner(self.data.company)
        if managers := await db.get_users_by_id(partner.partner_id):
            for manager in managers:
                await db.update_user(manager.user_id, None)
        await db.delete_partner(self.data.company)
        return "Менеджеры отвязаны. Партнёр удалён."
