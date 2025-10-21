# windshield_app
 
Веб-сервис студии по оклейке лобовых стекол автомобилей защитной пленкой. 

Проект включает в себя несколько модулей:
* Парсер для получения размеров стекол различных автомобилей и их изображений;
* База данных;
* Telegram-бот для удобного взаимодействия;
* Приложение выполняющее расчет
* Веб-сайт (TO DO) 

Реализована возможность добавления партнёров получающих специальные условия.
При выборе автомобиля сервис проверяет в БД размер лобового стекла данной модели, количество необходимого материала, а так же степень сложности выполняемой работы. 
Далее высчитывает цену оклейки стекла, учитывая сложность работ и страну производства плёнки.

База данных реализована на SQLite под управлением Tortoise ORM.
ТГ-бот написан на aiogram 3.2.
Веб-сайт реализован на FastAPI
.
Зависимости: pip install -r requirements.txt
Запуск сервера: uvicorn main:app --reload

Сервис находится в разработке, но уже выполняет базовый функционал. 
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
