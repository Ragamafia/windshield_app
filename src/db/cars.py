import uuid
from typing import Type

from tortoise.models import Model

from src.db.base import BaseDB
from src.db.table import BrandDBModel, ModelDBModel, GenDBModel
from logger import logger

class Car(BaseDB):
    brand: Type[Model] = BrandDBModel
    model: Type[Model] = ModelDBModel
    gen: Type[Model] = GenDBModel

    @BaseDB.ensure_car
    async def put_brand(self, brand_name):
        if not await self.brand.filter(brand=brand_name).exists():
            await self.brand.create(
                id=uuid.uuid4(),
                brand=brand_name
            )
            logger.info(f'Added brand: {brand_name}')

    @BaseDB.ensure_car
    async def put_model(self, brand, model):
        if not await self.model.filter(brand=brand, model=model).exists():
            await self.model.create(
                id=uuid.uuid4(),
                brand=brand,
                model=model
            )
            logger.info(f'Added model: {brand} {model}')

    @BaseDB.ensure_car
    async def put_gen(self, brand, model, year_start, year_end, gen, restyle):
        if not await self.gen.filter(
                brand=brand,
                model=model,
                year_start=year_start,
                year_end=year_end,
                gen=gen,
                restyle=restyle
        ).exists():

            await self.gen.create(
                id=uuid.uuid4(),
                brand=brand,
                model=model,
                year_start=year_start,
                year_end=year_end,
                gen=gen,
                restyle=restyle,
        )
            logger.info(f'Added: {brand} {model}, {year_start}-{year_end}')


    @BaseDB.ensure_car
    async def get_car(self, brand, model, gen):
        return await self.model.filter(
            brand=brand,
            model=model,
            gen=gen
        )


car: Car = Car()