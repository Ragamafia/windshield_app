import json
from pathlib import Path

from aiogram import types
from aiogram.filters import Command

from db.cars import car
from config import cfg

root = Path().cwd().parent.parent
path_to_base = root / "data/base.json"

with open(path_to_base, 'r', encoding='utf-8') as file:
    data = json.load(file)


def register_main_handlers(bot):
    user_states = {}
    models_list = []

    @bot.router.message(Command(commands=['start']))
    async def start_command(message: types.Message):

        models_list.clear()
        for brand, models in data.items():
            for model in models:
                models_list.append((brand, model))

        if not models_list:
            await message.answer("Нет необработанных автомобилей.")
            return

        await next_model(message)

    async def next_model(message):
        if not models_list:
            await message.answer("Processing complete.")
            return

        brand, model = models_list.pop(0)
        user_id = message.from_user.id
        user_states[user_id] = {'brand': brand, 'model': model}
        await message.answer(f"Введите уровень сложности для {brand.upper()} {model.upper()} (1 - 10):")

        if level := message.text:
            await car.put_car(
                brand,
                model,
                level,
            )


    @bot.router.message()
    async def handler_level(message: types.Message):
        user_id = message.from_user.id
        state = user_states.get(user_id)

        if not state:
            await message.answer("Please, send /start to begin.")
            return

        text = message.text.strip()

        try:
            level = int(text)
            if 1 <= level <= 10:
                brand = state['brand']
                model = state['model']
                await message.answer(f"Записана сложность для {brand.upper()} {model.upper()}: {level}")
                del user_states[user_id]
                await next_model(message)
            else:
                await message.answer("Пожалуйста, введите число от 1 до 10.")
        except ValueError:
            await message.answer("Пожалуйста, введите ЧИСЛОВОЕ значение от 1 до 10.")