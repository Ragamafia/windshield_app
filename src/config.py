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

    headers: dict = {
        "User-Agent": UserAgent().random
    }

    scheme: str = ''
    proxy_user: str = ''
    proxy_pass: str = ''
    proxy_host: str = ''
    proxy_port: str = ''

    bot_token: str = ''

    proxy_check_timeout: int = 60
    request_attempts: int = 5
    WORKERS_COUNT: int = 10

    sql_lite_db_path: Path = Path("../data/database.db")
    path_to_json_base: Path = Path("../data/base.json")
    path_to_json_hard: Path = Path("../data/hard.json")
    path_to_json_common: Path = Path("../data/glasses.json")
    path_to_update_base: Path = Path("../data/update_base.json")
    path_to_images: Path = Path("../data/images/")

    templates: Path = Path("app/templates")

    db_batch: int = 1
    db_offset: int = 0

    price_pm_usa: int = 8000
    price_pm_korea: int = 4000

    caf_small: float = 1.3
    caf_middle: float = 1.5
    caf_big: float = 1.7

    max_size_small: int = 1299

    min_size_middle: int = 1300
    max_size_middle: int = 1599

    min_size_big: int = 1600

    install_easy: int = 12000
    install_medium: int = 14000
    install_hard: int = 20000


cfg = Config()