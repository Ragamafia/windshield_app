from typing import Type

from tortoise.models import Model

from src.db.base import BaseDB
from src.db.table import CarDBModel


class Car(BaseDB):
    model: Type[Model] = CarDBModel

    @BaseDB.ensure_car
    async def put_car(self, brand, model, level):
        await self.model.create(
            brand=brand,
            model=model,
            glass_difficulty_level=level,
        )

    @BaseDB.ensure_car
    async def get_car(self, brand, model):
        return await self.model.filter(
            brand=brand,
            model=model,
        )


car: Car = Car()