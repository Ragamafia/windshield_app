from tortoise import Tortoise

from config import cfg


class BaseDB:
    # async def setup_db(self):
    #     await Tortoise.init(
    #         db_url=f"sqlite://{cfg.sql_lite_db_path}",
    #         modules={'models': ['db.table']}
    #     )
    #     await Tortoise.generate_schemas()

    async def setup_db(self):
        await Tortoise.init(
            db_url=f"sqlite://{cfg.sql_lite_db_path}",
            modules={'models': ['db.table']}
        )
        await Tortoise.generate_schemas()
