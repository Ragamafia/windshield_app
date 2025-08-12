import asyncio
from typing import Type

from tortoise.models import Model

from src.db.base import BaseDB
from src.db.table import BrandDBModel, ModelDBModel, GenDBModel, User
from logger import logger
from config import cfg


class DataBaseController(BaseDB):
    brand: Type[Model] = BrandDBModel
    model: Type[Model] = ModelDBModel
    gen: Type[Model] = GenDBModel

    user: Type[Model] = User

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
    async def get_model_to_parse(self):
        async with self.model_lock:
            if model := await self.model.filter(processed=False).first():
                await self.model.filter(id=model.id).update(processed=True)
                return model.brand, model.model

    @BaseDB.ensure_car
    async def get_gen_to_parse(self):
        async with self.gen_lock:
            if gen := await self.gen.filter(processed=False).first():
                await self.gen.filter(id=gen.id).update(processed=True)
                return gen.brand, gen.model, gen.glass_id

    @BaseDB.ensure_car
    async def get_images_for_check(self):
        async with self.gen_lock:
            result = []
            if cars := await self.gen.filter().all():
                for car in cars:
                    result.append([car.brand, car.model, car.glass_id, car.year_start, car.year_end])
            return result


    @BaseDB.ensure_car
    async def get_brands(self):
        return await self.brand.filter().all()

    @BaseDB.ensure_car
    async def get_models(self, brand):
        return await self.model.filter(brand=brand)

    @BaseDB.ensure_car
    async def get_gens(self, brand, model):
        return await self.gen.filter(brand=brand, model=model)

    @BaseDB.ensure_car
    async def get_gen(self, brand, model, year_start):
        if car := await self.gen.filter(brand=brand, model=model, year_start=year_start).first():
            return car.gen

    @BaseDB.ensure_car
    async def get_glass_id(self, brand, model, years):
        year_start = years.split("-")[0]
        if car := await self.gen.filter(brand=brand, model=model, year_start=year_start).first():
            return car.glass_id


    @BaseDB.ensure_car
    async def put_brands(self, brand):
        if not await self.brand.filter(brand=brand).exists():
            await self.brand.create(brand=brand)
            logger.info(f'Create brand: {brand}')

    @BaseDB.ensure_car
    async def put_model(self, brand, model):
        if not await self.model.filter(brand=brand, model=model).exists():
            await self.model.create(brand=brand, model=model)
            logger.info(f'Added model: {brand} {model}')

    @BaseDB.ensure_car
    async def put_gen(self, brand, model, glass_id, year_start, year_end, gen, restyle):
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
            logger.info(f'Added gen: {brand} {model} {year_start}-{year_end}. ID {glass_id}')

    @BaseDB.ensure_car
    async def put_size(self, glass_id, height, width):
        if car := await self.gen.filter(glass_id=glass_id).first():
            if not car.height:
                car.height = height
                car.width = width
                await car.save()
                logger.info(f'Update size for ID {glass_id}')


    @BaseDB.ensure_car
    async def get_model_info(self):
        async with self.gen_lock:
            if car := await self.gen.filter(level=False, year_start__gte=cfg.year_start).first():
                gens = await self.gen.filter(level=False, brand=car.brand, model=car.model, year_start__gte=cfg.year_start).order_by("year_start")
                groups = {}
                for gen in gens:
                    if gen.gen not in groups:
                        groups[gen.gen] = [gen]
                    else:
                        groups[gen.gen].append(gen)
                fixed = []
                for group in groups.values():
                    levels = [i.difficulty for i in group]
                    if len(set(levels)) == 1:
                        level = levels[0]
                    else:
                        level = None
                    fixed.append({
                        "ids": [i.glass_id for i in group],
                        "years": f"{group[0].year_start}-{group[0].year_end}",
                        "gen": group[0].gen,
                        "level": level,
                    })

                result = {
                    "brand": gens[0].brand if gens else "",
                    "model": gens[0].model if gens else "",
                    "groups": fixed,
                }
                return result

    @BaseDB.ensure_car
    async def update_level(self, brand, model, gen, level):
        if cars := await self.gen.filter(brand=brand, model=model, gen=gen).all():
            info = {}
            for car in cars:
                car.difficulty = level
                await car.save()
                await self.gen.filter(id=car.id).update(level=True)

                if car.model not in info:
                    info[car.model] = [f"{car.year_start}-{car.year_end}"]
                else:
                    info[car.model].append(f"{car.year_start}-{car.year_end}")

                logger.debug(f"Difficulty set for {brand} {model} {car.year_start}-{car.year_end} - {level}")

            return info

    @BaseDB.ensure_car
    async def count_brands(self):
        return len(await self.brand.filter().all())

    @BaseDB.ensure_car
    async def count_models(self):
        return len(await self.model.filter().all())

    @BaseDB.ensure_car
    async def count_level_true(self):
        return len(await self.gen.filter(level=True).all())

    @BaseDB.ensure_car
    async def count_level_false(self):
        return len(await self.gen.filter(level=False).all())

    @BaseDB.ensure_car
    async def count_gen(self):
        return len(await self.gen.filter().all())

    @BaseDB.ensure_car
    async def _delete(self):
        car = await self.user.filter(user_id=328216592).first()
        await car.delete()
        await car.save()


    @BaseDB.ensure_car
    async def create_user(self, user_id, username, first_name, admin: bool):
        await self.user.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            admin=admin
        )
        if user := await self.user.filter(user_id=user_id).first():

            result = {}
            result["user_id"] = user.user_id
            result["username"] = user.username
            result["first_name"] = user.first_name
            result["admin"] = user.admin

            return result


    @BaseDB.ensure_car
    async def create_admin(self, user):
        await self.user.create(
            admin=True,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

    @BaseDB.ensure_car
    async def get_user(self, user_id):
        if user := await self.user.filter(user_id=user_id).first():
            return user

    @BaseDB.ensure_car
    async def get_size(self, glass_id):
        if car := await self.gen.filter(glass_id=glass_id).first():
            return car.height, car.width


db: DataBaseController = DataBaseController()