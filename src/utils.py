import json
import asyncio
import random
from typing import Type

from tortoise.models import Model
from PIL import Image
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from src.db.table import GenDBModel
from src.db.base import BaseDB
from src.db.ctrl import db
from logger import logger
from config import cfg


class CheckerImage(BaseDB):
    gen: Type[Model] = GenDBModel

    async def get(self, url):
        async with ClientSession(headers=cfg.headers) as self.session:
            return await self.request("GET", url)

    async def request(self, method, url, attempts=cfg.request_attempts, **kwargs):
        async with self.session.request(method, url, **kwargs) as response:
            if response.status < 300:
                try:
                    return await response.text()
                except:
                    return await response.read()
            elif response.status == 429:
                await asyncio.sleep(random.randint(30, 60))
            elif response.status == 404:
                return
            else:
                attempts -= 1
                if attempts:
                    return await self.request(method, url, attempts, **kwargs)

    async def check_image(self, brand, model, id, year_start, year_end):
        save_dir = cfg.path_to_images / brand / model / id
        save_dir.mkdir(parents=True, exist_ok=True)
        image_path = save_dir / "img.jpg"

        if image_path.exists():
            try:
                with Image.open (image_path) as file:
                    file.verify()
                    logger.debug(f'Image for {brand} {model} {year_start}-{year_end} already exists')
            except:
                await self._download_image(image_path, brand, model, id, year_start, year_end)

        else:
            await self._download_image(image_path, brand, model, id, year_start, year_end)

    async def _download_image(self, image_path, brand, model, id, year_start, year_end):
        page = await self.get(f"{cfg.BASE_URL}/{brand}/{model}/{id}")
        try:
            soup = BeautifulSoup(page, "html.parser")
        except TypeError as e:
            print(f'ERROR! {e}')
            return

        image = soup.find('img', {"class": "fluid"})
        image = await self.get(image['src'])

        with open(image_path, 'wb') as file:
            file.write(image)
            logger.success(f'Save new image: {brand} {model} {year_start}-{year_end}')


def json_to_dict(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        json_str = file.read()
        dict_list = json.loads(json_str)
    return dict_list

def dict_to_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        print(f'Data saved in {file_path}')


checker: CheckerImage = CheckerImage()


class Calculate:
    height: int | None
    width: int | None
    difficulty: int | None

    async def _get_size(self, glass_id):
        self.height, self.width = await db.get_size(glass_id)
        return self.height, self.width
