from typing import Literal

from config import cfg


def get_cf_by_width(width):
    if width <= cfg.max_size_small:
        return cfg.caf_small
    elif cfg.min_size_middle <= width <= cfg.max_size_middle:
        return cfg.caf_middle
    elif cfg.min_size_big <= width:
        return cfg.caf_big


class CarGlass:
    width: int
    film_type: Literal['usa', 'korea']

    def __init__(self, width, high_level):
        self.width = width
        self.high_level = high_level


    def _get_price(self, film_type: Literal['usa', 'korea']):
        return self._get_work_price() + self._get_film_price(film_type)

    def _get_work_price(self):
        if self.high_level:
            return cfg.install_hard
        else:
            return cfg.install_medium

    def _get_film_price(self, film_type: Literal['usa', 'korea']):
        film_price = cfg.price_pm_usa if film_type == "usa" else cfg.price_pm_korea
        return film_price * get_cf_by_width(self.width)

    def get_prices(self):
        return self._get_price("usa"), self._get_price("korea")
