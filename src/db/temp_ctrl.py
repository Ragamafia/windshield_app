import asyncio
from typing import Type

from tortoise.models import Model

from db.temp_base import TempBaseDB
from db.temp_table import TempDifficulty
from logger import logger


class TempDataBaseController(TempBaseDB):
    difficulty: Type[Model] = TempDifficulty

    difficulty_lock: asyncio.Lock()

    def __init__(self):
        super().__init__()
        self.difficulty_lock = asyncio.Lock()

    async def put_difficulty(self, glass_id, difficulty):
        if difficulty is not None:
            if not await self.difficulty.filter(glass_id=glass_id).exists():
                await self.difficulty.create(glass_id=glass_id, difficulty=difficulty)
                logger.info(f'Put new difficulty: {glass_id} {difficulty}')
            else:
                logger.warning(f'Difficulty already exists: {glass_id} {difficulty}')
        else:
            print("dif None")

    async def get_difficulty(self):
        return await self.difficulty.all()


temp_db: TempDataBaseController = TempDataBaseController()
