import asyncio
from typing import Type
from collections import defaultdict

from tortoise.models import Model

from db.base import BaseDB
from db.table import BrandDBModel, ModelDBModel, CarDBModel, Users, Partner, BodyDBModel
from logger import logger
from config import cfg


class DataBaseController(BaseDB):
    brands: Type[Model] = BrandDBModel
    models: Type[Model] = ModelDBModel
    cars: Type[Model] = CarDBModel
    users: Type[Model] = Users
    partner: Type[Model] = Partner
    body: Type[Model] = BodyDBModel

    brand_lock: asyncio.Lock()
    model_lock: asyncio.Lock()
    car_lock: asyncio.Lock()

    def __init__(self):
        super().__init__()
        self.brand_lock = asyncio.Lock()
        self.model_lock = asyncio.Lock()
        self.car_lock = asyncio.Lock()

    async def get_brand_to_parse(self):
        async with self.brand_lock:
            if brand := await self.brands.filter(processed=False).first():
                await self.brands.filter(id=brand.id).update(processed=True)
                return brand.brand

    async def get_model_to_parse(self):
        async with self.model_lock:
            if model := await self.models.filter(processed=False).first():
                await self.models.filter(id=model.id).update(processed=True)
                return model.brand, model.model

    # async def get_group_all_cars(self):
    #         if all_cars := await self.cars.filter().all():
    #             groups = defaultdict(list)
    #             for models in all_cars:
    #                 key = (models.brand, models.model)
    #                 groups[key].append(models)
    #
    #             return list(groups.values())
    #
    # async def get_cars_without_image(self, brand, model) -> list[list]:
    #     async with self.car_lock:
    #         result = []
    #         if models := await self.cars.filter(brand=brand, model=model, img_received=False).all():
    #             for car in models:
    #                 result.append([car.brand, car.model, car.glass_id])
    #
    #         return result


    async def images_received(self, id):
        await self.cars.filter(glass_id=id).update(img_received=True)

    async def get_brands(self, letter: str = None):
        if letter:
            return await self.brands.filter(brand__startswith=letter).all().order_by('brand')
        else:
            return await self.brands.filter().all().order_by('brand')

    async def get_models(self, brand):
        return await self.models.filter(brand=brand).order_by('model')

    async def get_gens(self, brand, model):
        return await self.cars.filter(brand=brand, model=model)

    async def get_car(self, brand, model, year_start, body):
        return await self.cars.filter(brand=brand, model=model, year_start=year_start, body=body).first()

    async def get_body(self, brand, model, year_start):
        return await self.cars.filter(brand=brand, model=model, year_start=year_start).all()

    async def get_body_id(self, body: str):
        if id := await self.body.filter(body=body).first():
            return id.id
        else:
            id = await self.body.create(body=body)
            return id.id

    async def get_body_name(self, id):
        if name := await self.body.filter(id=id).first():
            return name.body

    async def get_all_body(self):
        return await self.body.all()

    async def get_avialable_models(self, brand, model_start_letter: str = None):
        if model_start_letter:
            return await self.cars.filter(brand=brand, model__startswith=model_start_letter).values_list("model", flat=True)
        else:
            return await self.cars.filter(brand=brand).distinct().values_list("model", flat=True)

    async def put_brands(self, brand):
        if not await self.brands.filter(brand=brand).exists():
            await self.brands.create(brand=brand)
            logger.info(f'Create brand: {brand}')

    async def put_model(self, brand, model):
        if not await self.models.filter(brand=brand, model=model).exists():
            await self.models.create(brand=brand, model=model)
            logger.info(f'Added model: {brand} {model}')

    async def put_gen(self, brand, model, glass_id, year_start, year_end, gen, restyle, body):
        async with self.car_lock:
            if not await self.cars.filter(glass_id=glass_id).exists():
                await self.cars.create(
                    brand=brand,
                    model=model,
                    glass_id=glass_id,
                    year_start=year_start,
                    year_end=year_end,
                    gen=gen,
                    restyle=restyle,
                    body=body
                )
                logger.info(f'Added gen: {brand} {model} {year_start}-{year_end}. ID {glass_id}')

    async def put_size(self, glass_id, height, width):
        async with self.car_lock:
            if car := await self.cars.filter(glass_id=glass_id).first():
                if height is not None:
                    car.height = height
                    car.width = width
                    await car.save()
                    await self.cars.filter(id=car.id).update(size_received=True)
                    logger.info(f'Put size for {car.brand} {car.model}, ID {glass_id}')
                else:
                    logger.warning(f'No size for {car.brand} {car.model}, ID {glass_id}')

    async def put_difficulty_not_processed(self, body_id, difficulty_level):
        if cars := await self.cars.filter(body=body_id, processed=False).all():
            for car in cars:
                car.difficulty = difficulty_level
                await car.save()
                await self.cars.filter(id=car.id).update(level_received=True)
                logger.debug(f'Difficulty set for {car.brand} {car.model} {car.year_start}-{car.year_end} - {difficulty_level}')


    async def get_model_info(self):
        async with self.car_lock:
            if car := await self.cars.filter(level=False, year_start__gte=cfg.year_start_search).first():
                gens = await self.cars.filter(level=False, brand=car.brand, model=car.model, year_start__gte=cfg.year_start_search).order_by("year_start")
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

    async def update_level(self, glass_id, level):
        if car := await self.cars.filter(glass_id=glass_id).first():
            car.difficulty = level
            await car.save()
            await self.cars.filter(id=car.id).update(level_received=True, processed=True)
            logger.success(f"Difficulty set for {car.brand} {car.model} {car.year_start}-{car.year_end} - {level}")
            return car


    async def count_cars(self):
        return await self.cars.all().count()


    async def create_user(self, user_id, username, first_name, admin: bool, is_manager: bool):
        await self.users.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            admin=admin,
            is_manager=is_manager
        )
        return await self.users.filter(user_id=user_id).first().values()

    async def get_users(self):
        return await self.users.all().order_by("first_name")

    async def get_managers(self):
        return await self.users.filter(is_manager=True).all().order_by("first_name")

    async def get_user(self, user_id):
        if user := await self.users.filter(user_id=user_id).first():
            return user

    async def get_users_by_id(self, id):
        return await self.users.filter(company_id=id).all()

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
