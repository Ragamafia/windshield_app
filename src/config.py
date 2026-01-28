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

    proxy: str = ''
    proxy_check_timeout: int = 60
    request_attempts: int = 10
    WORKERS_COUNT: int = 3

    sql_lite_db_path: Path = Path("../data/database.db")
    sql_lite_temp_db_path: Path = Path("../data/tempdatabase.db")
    path_to_images: Path = Path("../data/images/")

    templates: Path = Path("app/templates")

    admins: list[int] = [1377785914, 1015877207] #1377785914,
    admin_url: str = "https://t.me/TonirStark"

    max_brand_list: int = 12
    max_models_list: int = 30

    min_level: int = 1
    max_level: int = 10

    year_start_search: int = 1998

    default_height: int = 900
    default_width: int = 1550
    default_setup: int = 12000

    price_pm_usa: int = 8000
    price_pm_korea: int = 4000

    setup: dict = {
        1: 8000,
        2: 9000,
        3: 10000,
        4: 11000,
        5: 12000,
        6: 13000,
        7: 14000,
        8: 16000,
        9: 18000,
        10: 20000
    }

    irkutsk_tz: str = "Asia/Irkutsk"


cfg = Config()
