# windshield_app
FastAPI used

Перед вами веб-сервис, предоставляющий информацию о цене оклейки защитной пленкой лобового стекла выбираемого автомобиля. 
Сервис находится в стадии разработки, но уже выполняет базовый функционал. 

При выборе автомобиля сервис проверяет в БД размер лобового стекла данной модели, а так же степень сложности выполняемой работы. 
После чего высчитывает цену оклейки стекла, учитывая количество потраченного материала и вида плёнки.

База данных автомобилей хранится в JSON-файле и структурирована по брендам, моделям и годам выпуска.

Веб-сайт реализован на FastAPI.
Зависимости: pip install -r requirements.txt
Запуск сервера: uvicorn main:app --reload

JSON с базой размеров стекол, а так же файл с особенно сложными в работе автомобилями размщается в корне проекта.

TO DO: 
- добавление поиска авто
- разработка телеграм-бота


___________________________________________________
You are viewing a web service that provides information about the price of applying protective film to the windshield of a selected vehicle.
The service is in development but already offers basic functionality.

When selecting a vehicle, the service checks in the database the size of the windshield for that model, as well as the complexity level of the work required.
It then calculates the cost of applying the film, taking into account the amount of material used and the type of film.

The vehicle database is stored in a JSON file and structured by brands, models, and years of manufacture.

The website is built with FastAPI.
Dependencies: pip install -r requirements.txt
To run the server: uvicorn main:app --reload

The JSON file with windshield sizes, as well as a file listing particularly complex vehicles, are located in the root of the project.

TO DO:

Add vehicle search functionality
Develop a Telegram bot
