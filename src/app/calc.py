from typing import Literal

from config import cfg


class Calculate:
    width: int
    difficulty: int
    film_type: Literal['usa', 'korea']

    def __init__(self, width, difficulty):
        self.width = width
        self.difficulty = difficulty

    def _get_price(self, film_type: Literal['usa', 'korea']):
        if difficulty := cfg.setup.get(self.difficulty):
            return difficulty + self._get_film_price(film_type)
        else:
            return cfg.default_setup + self._get_film_price(film_type)

    def _get_film_price(self, film_type: Literal['usa', 'korea']):
        film_price = cfg.price_pm_usa if film_type == "usa" else cfg.price_pm_korea
        if self.width:
            return int(film_price * self.width / 1000)
        else:
            return int(film_price * cfg.default_width / 1000)

    async def get_prices(self):
        return self._get_price("usa"), self._get_price("korea")

    async def get_only_film_prices(self):
        return self._get_film_price("usa"), self._get_film_price("korea")
