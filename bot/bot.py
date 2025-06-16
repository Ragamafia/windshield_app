import json

from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor


API_TOKEN = ''

root = Path.cwd()
path_to_base = root.parent / 'app/base.json'

with open(path_to_base, 'r', encoding='utf-8') as f:
    data = json.load(f)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_states = {}
models_list = []


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    global models_list
    models_list.clear()
    for brand, models in data.items():
        for model in models:
            models_list.append((brand, model))
    if not models_list:
        await message.answer("База данных пуста.")
        return

    await process_next_model(message)


async def process_next_model(message):
    if not models_list:
        await message.answer("Обработка завершена.")
        return

    brand, model = models_list.pop(0)
    # Сохраняем текущую модель в состоянии пользователя
    user_id = message.from_user.id
    user_states[user_id] = {'brand': brand, 'model': model}

    await message.answer(f"Введите категорию сложности для {brand.upper()} {model.upper()} (1 - 5):")


@dp.message_handler()
async def handle_category(message: types.Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state:
        await message.answer("Пожалуйста, начните командой /start.")
        return

    text = message.text.strip()

    try:
        category_number = int(text)
        if 1 <= category_number <= 5:
            brand = state['brand']
            model = state['model']
            await message.answer(f"Категория сложности для {brand.upper()} {model.upper()}: {category_number}")
            # Удаляем состояние пользователя после обработки
            del user_states[user_id]
            # Переходим к следующей модели
            await process_next_model(message)
        else:
            await message.answer("Пожалуйста, введите число от 1 до 5.")
    except ValueError:
        await message.answer("Пожалуйста, введите числовое значение от 1 до 5.")


if __name__ == '__main__':
    executor.start_polling(dp)