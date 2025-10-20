from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.partners.main import PartnerCallBackController
from bot.partners.states import *
from db.ctrl import db
from models import User


def register_partners_handlers(bot):
    @bot.router.callback_query(F.data.startswith("set_partners"))
    @bot.authorize
    async def partners_callback_handler(callback: CallbackQuery, user: User):
        data = PartnerCallBackController(callback, user)
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)

    @bot.router.callback_query(F.data.startswith("add"))
    async def add_handler(callback: CallbackQuery, state: FSMContext):
        await callback.message.answer("Введите нового партнёра:\n(Имя или название фирмы)")
        await state.set_state(EditPartner.name)

    @bot.router.message(EditPartner.name)
    async def name_handler(message: Message, state: FSMContext):
        await state.update_data(name=message.text)
        await message.answer("Введите скидку партнёра (в процентах):")
        await state.set_state(EditPartner.discount)

    @bot.router.message(EditPartner.discount)
    async def discount_handler(message: Message, state: FSMContext):
        data = await state.get_data()
        name = data["name"]
        discount = message.text
        try:
            await db.put_partner(name, discount)
            await message.answer(f"✅ Сохранено!\n\n"
                                 f"Партнёр: {name}\n"
                                 f"Дисконт: {discount}%")
            await state.clear()
        except Exception as e:
            await message.answer(f"Пожалуйста, введите действительное число в процентах")

    @bot.router.callback_query(F.data.startswith("partners"))
    @bot.authorize
    async def view_partners(callback: CallbackQuery, user: User):
        data = PartnerCallBackController(callback, user)
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)

    @bot.router.callback_query(F.data.startswith("partner"))
    @bot.authorize
    async def view_partner(callback: CallbackQuery, user: User):
        data = PartnerCallBackController(callback, user)
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)
