import asyncio
from typing import Type

from tortoise.models import Model

from db.base import BaseDB
from db.table import BrandDBModel, ModelDBModel, GenDBModel, Users, Partner
from logger import logger
from config import cfg


class DataBaseController(BaseDB):
    brand: Type[Model] = BrandDBModel
    model: Type[Model] = ModelDBModel
    gen: Type[Model] = GenDBModel
    users: Type[Model] = Users
    partner: Type[Model] = Partner

    brand_lock: asyncio.Lock()
    model_lock: asyncio.Lock()
    gen_lock: asyncio.Lock()

    def __init__(self):
        super().__init__()
        self.brand_lock = asyncio.Lock()
        self.model_lock = asyncio.Lock()
        self.gen_lock = asyncio.Lock()

    async def no_brands(self):
        empty = await self.brand.first()
        if empty is None:
            return True

    async def get_brand_to_parse(self):
        async with self.brand_lock:
            if brand := await self.brand.filter(processed=False).first():
                await self.brand.filter(id=brand.id).update(processed=True)
                return brand.brand

    async def get_model_to_parse(self):
        async with self.model_lock:
            if model := await self.model.filter(processed=False).first():
                await self.model.filter(id=model.id).update(processed=True)
                return model.brand, model.model

    async def get_gen_to_parse(self):
        async with self.gen_lock:
            if gen := await self.gen.filter(processed=False).first():
                await self.gen.filter(id=gen.id).update(processed=True)
                return gen.brand, gen.model, gen.glass_id

    async def get_images_for_check(self):
        async with self.gen_lock:
            result = []
            if cars := await self.gen.filter().all():
                for car in cars:
                    result.append([car.brand, car.model, car.glass_id])
            return result

    async def get_brands(self):
        return await self.brand.filter().all()

    async def get_models(self, brand):
        return await self.model.filter(brand=brand)

    async def get_avialable_models(self, brand):
        return await self.gen.filter(brand=brand).values_list("model", flat=True)

    async def get_gens(self, brand, model):
        return await self.gen.filter(brand=brand, model=model)

    async def get_car(self, brand, model, year_start):
        return await self.gen.filter(brand=brand, model=model, year_start=year_start).first()


    async def put_brands(self, brand):
        if not await self.brand.filter(brand=brand).exists():
            await self.brand.create(brand=brand)
            logger.info(f'Create brand: {brand}')

    async def put_model(self, brand, model):
        if not await self.model.filter(brand=brand, model=model).exists():
            await self.model.create(brand=brand, model=model)
            logger.info(f'Added model: {brand} {model}')

    async def put_gen(self, brand, model, glass_id, year_start, year_end, gen, restyle):
        if not await self.gen.filter(
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

    async def put_size(self, glass_id, height, width):
        if car := await self.gen.filter(glass_id=glass_id).first():
            if not car.height:
                car.height = height
                car.width = width
                await car.save()
                logger.info(f'Update size for ID {glass_id}')

    async def get_model_info(self):
        async with self.gen_lock:
            if car := await self.gen.filter(level=False, year_start__gte=cfg.year_start_search).first():
                gens = await self.gen.filter(level=False, brand=car.brand, model=car.model, year_start__gte=cfg.year_start_search).order_by("year_start")
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

    async def update_level(self, brand, model, gen, level):
        if cars := await self.gen.filter(brand=brand, model=model, gen=gen).all():
            for car in cars:
                car.difficulty = level
                await car.save()
                await self.gen.filter(id=car.id).update(level=True)
                logger.debug(f"Difficulty set for {brand} {model} {car.year_start}-{car.year_end} - {level}")
            return cars[0]

    async def count_models(self):
        return await self.model.all().count()

    async def count_cars(self):
        return await self.gen.all().count()

    async def count_processed_level(self, level: bool):
        return await self.gen.filter(level=level).all().count()


    async def create_user(self, user_id, username, first_name, admin: bool):
        await self.users.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            admin=admin
        )
        return await self.users.filter(user_id=user_id).first().values()

    async def get_users(self):
        return await self.users.all().order_by("first_name")

    async def get_user(self, user_id):
        if user := await self.users.filter(user_id=user_id).first():
            return user

    async def get_users_by_id(self, id):
        if users := await self.users.filter(company_id=id).all():
            return users

    async def update_user(self, user_id, company_id):
        if user := await self.users.filter(user_id=user_id).first():
            user.company_id = company_id
            await user.save()
            logger.info(f'User updated: {user.first_name}.')

    async def delete_user(self, user_id):
        if user := await self.users.filter(user_id=user_id).first():
            await user.delete()


    async def get_partners(self):
        return await self.partner.all().order_by("name")

    async def get_partner(self, name):
        return await self.partner.filter(name=name).first()

    async def get_partner_by_id(self, id):
        return await self.partner.filter(partner_id=id).first()

    async def delete_partner(self, name):
        if partner := await self.partner.filter(name=name).first():
            await partner.delete()

    async def put_partner(self, name, discount):
        if not await self.partner.filter(name=name).exists():
            await self.partner.create(name=name, discount=discount)
            logger.info(f'Create new partner: {name}')
        elif partner := await self.partner.filter(name=name).first():
            partner.discount = discount
            await partner.save()
            logger.info(f'Partner updated: {name}. New discount: {discount}%')


db: DataBaseController = DataBaseController()
