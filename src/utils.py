import asyncio
import random

from PIL import Image
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from models import User
from db.base import BaseDB
from db.ctrl import db
from logger import logger
from config import cfg


class CheckerImage(BaseDB):
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

    async def check_image(self, brand, model, id):
        save_dir = cfg.path_to_images / brand / model / id
        save_dir.mkdir(parents=True, exist_ok=True)
        image_path = save_dir / "img.jpg"

        if image_path.exists():
            try:
                with Image.open (image_path) as file:
                    file.verify()
                    logger.debug(f"Image for {brand} {model} already exists")
            except:
                await self._download_image(image_path, brand, model, id)

        else:
            await self._download_image(image_path, brand, model, id)

    async def _download_image(self, image_path, brand, model, id):
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
            logger.success(f"Save new image: {brand} {model}")


async def check_discount(user: User):
    user = await db.get_user(user.user_id)
    if company := await db.get_partner_by_id(user.company_id):
        return company.name, company.discount
    else:
        logger.warning(f"User {user.username} not tied to the company")
        return False
