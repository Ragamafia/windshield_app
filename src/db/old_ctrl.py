import asyncio
from typing import Type

from tortoise.models import Model

from db.base import BaseDB
from db.old_table import GenDBModel


class DataBaseController(BaseDB):
    gens: Type[Model] = GenDBModel

    gens_lock: asyncio.Lock()

    def __init__(self):
        super().__init__()
        self.gens_lock = asyncio.Lock()

    async def get_all_cars(self):
        return await self.gens.all().order_by("brand")


old_db: DataBaseController = DataBaseController()
