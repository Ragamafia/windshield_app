import sqlite3
from functools import wraps
from typing_extensions import Type

from tortoise import Tortoise



def ensure_car(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.inited:
            await self.setup_db()
        return await func(self, *args, **kwargs)
    return wrapper


class BaseDB:
    name: str = ""
    inited: bool = False
    model: Type[Model]
    ensure_client: callable = ensure_client
    primary_key: str = "id"

    def __init__(self, prefix: str = None):
        if prefix:
            self.name = prefix

    async def setup_db(self):
        if self.name:
            filename = cfg.sql_lite_db_path.with_suffix(f".{self.name}.db")
        else:
            filename = cfg.sql_lite_db_path
        await Tortoise.init(
            db_url=f"sqlite://{filename}",
            modules={'models': ['db.tables']}
        )
        BaseDB.inited = True
        await Tortoise.generate_schemas()