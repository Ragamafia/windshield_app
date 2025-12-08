# windshield_app

Windshield App — сервис студии по оклейке лобовых стёкол автомобилей защитной плёнкой.
Проект включает Telegram-бот, модуль расчётов и парсер для получения размеров стекол и изображений автомобилей.
Реализована возможность добавления партнёров получающих специальные условия. Вы можете создавать компании, привязывать к ним менеджеров и юзеры с соответствующими ID будут получать в боте спец-цену.
При выборе автомобиля сервис проверяет в БД размер лобового стекла данной модели, количество необходимого материала, а так же степень сложности выполняемой работы. 
Далее высчитывает цену оклейки стекла, учитывая сложность работ и страну производства плёнки.
Сервис находится в разработке, но уже выполняет основной функционал: от выбора автомобиля до расчёта стоимости оклейки.

🔍 1. Парсер стекол и изображений

Автоматически собирает размеры лобовых стёкол автомобилей, изображения машин, информацию о поколениях и моделях.
Работает асинхронно.

🗄️ 2. База данных

В БД хранятся:

марки / модели / поколения / годы;
размеры стекол;
сложность работ;
партнёрские компании и менеджеры;
специальные цены и скидки;

Используется SQLite + Tortoise ORM.

🤖 3. Telegram-бот

Бот для удобного взаимодействия с системой:
пошаговый выбор автомобиля;
выбор марки → модели → поколения;
расчёт стоимости оклейки;
показ изображений;
доступ к спец-ценам партнёров;
админ-панель для редактирования данных;

Создан на aiogram 3.2.

🧮 4. Модуль расчёта

Расчитывает:

площадь стекла;
расход материала;
стоимость оклейки;
коэффициент сложности;
влияние страны производства плёнки;

🌐 5. Web API (FastAPI)

REST-интерфейс для интеграции с фронтендом и внешними системами.
Функционал сайта будет расширяться (TO DO).

🧩 Система партнёров

Реализована система компаний и менеджеров:

создавайте партнёрские компании;
добавляйте менеджеров;
пользователи с привязанными ID автоматически получают специальные условия в Telegram-боте;

🛠️ Технологии

Python 3.13

FastAPI

aiogram 3.2

SQLite + Tortoise ORM

Pydantic

Uvicorn
___________________________________________________

Установка:

git clone https://github.com/Ragamafia/windshield_app.git

cd windshield_app

python -m venv env

source env/bin/activate

pip install -r requirements.txt
___________________________________________________

Запуск:

python main.py

(Сервер запускается из main.py)

___________________________________________________

You are looking at a web service for a car windshield wrapping studio using protective film.
The project includes a parser to obtain the dimensions of various car windshields, a database, a website built with FastAPI, and a Telegram bot for convenient interaction.

When selecting a vehicle, the service checks the database for the size of the windshield for that specific model, calculates the required amount of material, and assesses the complexity of the work.
It then computes the price of wrapping the windshield, taking into account the complexity of the work and the country of manufacture of the film.

The database is implemented on SQLite managed via Tortoise ORM.
The Telegram bot is written using aiogram 3.2.
The website is built with FastAPI.

Dependencies: pip install -r requirements.txt
Server launch: uvicorn main:app --reload

The service is still in development but already provides basic functionality.
