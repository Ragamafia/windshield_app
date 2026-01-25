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
