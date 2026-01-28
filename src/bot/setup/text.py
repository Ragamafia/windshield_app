from db.ctrl import db


class Text():

    def __init__(self, data):
        self.data = data

    async def get_select_body_text(self):
        if self.data.action == "select_body" and not self.data.id:
            return ("Выберите тип кузова для выбора уровня сложности.\n\n" 
                   "❗❗❗ ️ВНИМАНИЕ  ❗❗❗\nCложность будет изменена ДЛЯ ВСЕХ АВТОМОБИЛЕЙ " 
                   "с выбранным кузовом, кроме тех, которые назначены вручную.\n")

        elif self.data.action == "select_body" and not self.data.difficulty:
            return ('Установите уровень сложности для кузова: '
                    f'"{await db.get_body_name(self.data.id)}"')

        else:
            return (f'✅ Сложность "{self.data.difficulty}" установлена для '
                    f'всех машин с кузовом "{await db.get_body_name(self.data.id)}" '
                    f'которые не были обработаны "вручную".\n')

    async def get_start_parse_text(self):
        return ("⚠️Пополнение базы данных новой информацией ⚠️\n\n"
                "Получение новых моделей автомобилей, отсутствующих размеров и "
                "недостающих изображений.\n\n"
                "Парсинг будет выполнен в фоновом режиме. "
                "По завершении работы вы получите информацию о новых данных.\n\n"
                "Для старта парсера нажмите ПРОДОЛЖИТЬ 🟢")
