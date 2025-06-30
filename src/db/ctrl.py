import asyncio
from typing import Type

from tortoise.models import Model

from src.db.base import BaseDB
from src.db.table import BrandDBModel, ModelDBModel, GenDBModel
from logger import logger


class DataBaseController(BaseDB):
    brand: Type[Model] = BrandDBModel
    model: Type[Model] = ModelDBModel
    gen: Type[Model] = GenDBModel

    brand_lock: asyncio.Lock()
    model_lock: asyncio.Lock()
    gen_lock: asyncio.Lock()

    def __init__(self):
        super().__init__()

        self.brand_lock = asyncio.Lock()
        self.model_lock = asyncio.Lock()
        self.gen_lock = asyncio.Lock()

    @BaseDB.ensure_car
    async def no_brands(self):
        empty = await self.brand.first()
        if empty is None:
            return True

    @BaseDB.ensure_car
    async def get_brand_to_parse(self):
        async with self.brand_lock:
            if brand := await self.brand.filter(processed=False).first():
                await self.brand.filter(id=brand.id).update(processed=True)
                return brand.brand

    @BaseDB.ensure_car
    async def get_model(self):
        async with self.model_lock:
            if model := await self.model.filter(processed=False).first():
                await self.model.filter(id=model.id).update(processed=True)
                if model is not None:
                    return model.brand, model.model

    @BaseDB.ensure_car
    async def get_gen(self):
        async with self.gen_lock:
            if gen := await self.gen.all():
                return len(gen)

    @BaseDB.ensure_car
    async def put_brands(self, brand):
        #if not await self.brand.filter(brand=brand).exists():
        await self.brand.create(brand=brand)
        logger.info(f'Added brand: {brand}')

    @BaseDB.ensure_car
    async def put_model(self, brand, model):
        if not await self.model.filter(brand=brand, model=model).exists():
            await self.model.create(
                brand=brand,
                model=model
            )
            logger.info(f'Added model: {brand} {model}')

    @BaseDB.ensure_car
    async def put_gens(self, brand, model, glass_id, year_start, year_end, gen, restyle):
        if not await self.gen.filter(
                brand=brand,
                model=model,
                glass_id=glass_id,
        ).exists():
            await self.gen.create(
                brand=brand,
                model=model,
                glass_id=glass_id,
                year_start=year_start,
                year_end=year_end,
                gen=gen,
                restyle=restyle
            )
            logger.info(f'Added gen: {brand} {model} {glass_id}')

    @BaseDB.ensure_car
    async def put_size(self, height, width):
        ...

    # @BaseDB.ensure_car
    # async def put_gens(self, brand, model, year_start, year_end, gen, restyle, img_id):
    #     if not await self.gen.filter(
    #             brand=brand,
    #             model=model,
    #             year_start=year_start,
    #             year_end=year_end,
    #             gen=gen,
    #             restyle=restyle
    #     ).exists():
    #
    #         await self.gen.create(
    #             brand=brand,
    #             model=model,
    #             year_start=year_start,
    #             year_end=year_end,
    #             gen=gen,
    #             restyle=restyle,
    #             img_id=img_id
    #     )
    #         logger.info(f'Added: {brand} {model}, {year_start}-{year_end}')

    @BaseDB.ensure_car
    async def delete(self, brand):
        await self.brand.filter(brand=brand).delete()


db: DataBaseController = DataBaseController()