import asyncio

from PIL import Image

from parser.car import MainParser
from logger import logger
from config import cfg


class ImagesParser(MainParser):

    def __init__(self, db):
        super().__init__()
        self.db = db

    async def run(self):
        async with await self.new_session() as self.session:
            if all_cars := await self.db.get_group_all_cars():
                for models in all_cars:
                    for model in models:
                        cars = await self.db.get_cars_without_image(model.brand, model.model)
                    task = [self._download_image(*car) for car in cars]
                    await asyncio.gather(*task)

    async def _download_image(self, brand, model, id):
        save_dir = cfg.path_to_images / brand / model / id
        save_dir.mkdir(parents=True, exist_ok=True)
        image_path = save_dir / "img.jpg"

        url = f"{cfg.BASE_URL}/{brand}/{model}/{id}"
        soup = await self._get_page(url)
        try:
            image = soup.find('img', {"class": "fluid"})
            image = await self.get(image['src'])
            with open(image_path, 'wb') as file:
                file.write(image)
                await self.db.images_received(id)
                logger.success(f'Save new image: {brand} {model} {id}')
        except:
            print(f"Can not find image {brand} {model} {id}")

    async def check_image(self, image_path, brand, model, id):
        if image_path.exists():
            try:
                with Image.open(image_path) as f:
                    f.verify()
                    logger.success(f'Image already exists: {brand} {model} {id}')
            except:
                await self._download_image(brand, model, id)
