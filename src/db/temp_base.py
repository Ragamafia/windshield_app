from tortoise import Tortoise

from config import cfg


class TempBaseDB:
    async def setup_db(self):
        await Tortoise.init(
            db_url=f"sqlite://{cfg.sql_lite_temp_db_path}",
            modules={'models': ['db.temp_table']}
        )
        await Tortoise.generate_schemas()
