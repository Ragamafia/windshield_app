from pydantic import BaseModel


class Config(BaseModel):
    price_pm_usa: int = 7700
    price_pm_korea: int = 4000

    caf_small: int = 1.3
    caf_middle: int = 1.5
    caf_big: int = 1.7

    max_size_small: int = 1299

    min_size_middle: int = 1300
    max_size_middle: int = 1599

    min_size_big: int = 1600


    install_medium: int = 20000
    install_hard: int = 25000


cfg = Config()