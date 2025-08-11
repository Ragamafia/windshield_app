from pathlib import Path

from pydantic_settings import BaseSettings
from fake_useragent import UserAgent


class Config(BaseSettings):

    class Config:
        env_file = "../env/.env"
        env_file_encoding = "utf-8"

    ## Main
    HOME_URL: str = "https://autosteklo.ru/"
    CITY: str = "moscow"
    BASE_URL: str = f"{HOME_URL.rstrip('/')}/{CITY}/steklo"

    headers: dict = {
        "User-Agent": UserAgent().random
    }

    bot_token: str = ''

    proxy_check_timeout: int = 60
    request_attempts: int = 10
    WORKERS_COUNT: int = 5

    sql_lite_db_path: Path = Path("../data/database.db")
    path_to_json_base: Path = Path("../data/base.json")
    path_to_images: Path = Path("../data/images/")

    templates: Path = Path("app/templates")

    admins: list[int] = [] #1377785914

    min_level: int = 1
    max_level: int = 10

    year_start: int = 1998

    default_height: int = 900
    default_width: int = 1550

    price_pm_usa: int = 8000
    price_pm_korea: int = 4000


cfg = Config()