from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.partners.main import PartnerCallBackController
from bot.partners.states import *
from db.ctrl import db
from models import User


def register_partners_handlers(bot):
    @bot.router.callback_query(F.data.startswith("partners:add"))
    async def add_handler(callback: CallbackQuery, state: FSMContext):
        await callback.message.answer("Введите новое имя или название фирмы:")
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
        except Exception:
            await message.answer(f"Пожалуйста, введите действительное число в процентах")
        await post_update(message)

    @bot.router.callback_query(F.data.startswith("partners:edit_discount"))
    async def update_discount_handler(callback: CallbackQuery, state: FSMContext):
        await callback.message.answer(f"Введите новую скидку (целое число в процентах).")
        await state.set_state(EditPartner.discount)
        name = callback.data.split("#")[1]
        await state.update_data(name=name.strip("*"))

    @bot.router.callback_query(F.data.startswith("partners:"))
    @bot.authorize
    async def partners_callback_handler(callback: CallbackQuery, user: User):
        data = PartnerCallBackController(callback, user)
        text = await data.text()
        keyboard = await data.keyboard()
        await callback.message.answer(text, reply_markup=keyboard)


    async def post_update(msg):
        fake_callback = CallbackQuery(id=str(msg.message_id),
                                      chat_instance=str(msg.chat.id),
                                      from_user=msg.from_user,
                                      data="partners:set_partners#*"
                                      )
        data = PartnerCallBackController(fake_callback, msg.from_user)
        text = await data.text()
        keyboard = await data.keyboard()
        await msg.answer(text, reply_markup=keyboard)
