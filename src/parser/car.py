import asyncio
import re

from parser.main import MainParser
from config import cfg
from logger import logger


class CarParser(MainParser):

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.started = True

    async def run(self):
        async with await self.new_session() as self.session:
            while self.started:
                if brand := await self.db.get_brand_to_parse():
                    if models := await self._parse_brand(brand):
                        task = [self.db.put_model(brand, model) for model in models]
                        await asyncio.gather(*task)

                elif model := await self.db.get_model_to_parse():
                    if result := await self._parse_model(*model):
                        sizes = [await self._parse_gen(*model, id["glass_id"]) for id in result]

                        task_put_gen = [self.db.put_gen(**res) for res in result]
                        task_download_image = [self._download_image(*model, id["glass_id"]) for id in result]
                        await asyncio.gather(*task_put_gen, *task_download_image)
                        task_put_size = [self.db.put_size(*size) for size in sizes]
                        await asyncio.gather(*task_put_size)

                else:
                    logger.success(f"Parsing complete. Total cars: {await self.db.count_cars()}.")
                    self.started = False

    async def get_new_brands(self):
        async with await self.new_session() as self.session:
            current_brands = await self.db.get_brands()
            len_current_brands = len(current_brands) if current_brands else 0
            if brands := await self._parse_all_brands():
                task = [self.db.put_brands(brand) for brand in brands]
                await asyncio.gather(*task)
                logger.success(f"Receive {len(brands) - len_current_brands} new brands.")
            else:
                raise RuntimeError("Can not get all brands. Aborting...")

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

    async def _parse_all_brands(self) -> list:
        soup = await self._get_page(cfg.HOME_URL)
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        brands = [i['href'].split('/', 3)[3] for i in data]
        return brands

    async def _parse_brand(self, brand) -> list:
        url = f"{cfg.BASE_URL}/{brand}"
        soup = await self._get_page(url)
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        models = [i['href'].split('/', 4)[4] for i in data]
        return models

    async def _parse_model(self, brand, model) -> list[dict]:
        url = f"{cfg.BASE_URL}/{brand}/{model}"
        soup = await self._get_page(url)

        results = []

        if cards := soup.find_all("div", {"class": "group-car-card"}):
            for card in cards:
                groups = card.find_all("div", {"class": "car-group"})
                for group in groups:
                    cars = group.find_all("a", {"class": "car-card"})
                    for car in cars:
                        results.append(await self.get_data(brand, model, card, car))
        else:
            cards = soup.find_all("div", {"class": "car-info"})
            for card in cards:
                results.append(await self.get_data(brand, model, card))

        return results

    async def get_data(self, brand, model, card, car=None):
        try:
            return {
                "brand": brand,
                "model": model,
                "glass_id": await self._parse_glass_id(card),
                ** await self._parse_years(card),
                ** await self._parse_generation(card),
                "body": await self._parse_body(card),
            }

        except Exception as e:
            print(f"Can not parse model for {brand} {model}:\n "
                  f"ERROR: {e}\n{card}")

    async def _parse_glass_id(self, card):
        try:
            tag = card.find('a', class_='car-card')
            id = tag["href"].split("/")[-1]
        except:
            id = card.parent.parent["href"].split("/")[-1]
        return id

    async def _parse_years(self, card):
        div = card.find("div", class_=["caption-year", "years"])
        years = div.text.split()

        try:
            start = int(years[2])
        except ValueError:
            start = None
        try:
            end = int(years[4])
        except ValueError:
            end = None

        return {
            "year_start": start,
            "year_end": end,
        }

    async def _parse_generation(self, card):
        span = card.find("span", {"class": "caption-generation"})
        if not span:
            span = card.find("div", {"class": "gens"})

        if match := re.search(r'(\d+)-й рестайлинг', span.text):
            restyle = int(match.group(1))
        else:
            restyle = 0

        gen = span.text.strip().split(',')
        print(f"GEN {gen}")
        for i in gen[0].split():
            if i.isdigit():
                gen = int(i)
            else:
                for a in i:
                    if a.isdigit():
                        gen = int(a)
        return {
            "gen": gen,
            "restyle": restyle
        }

    async def _parse_body(self, card):
        div = card.find("div", class_=["name"])
        if not div:
            div = card.find("div", class_=["serie"])

        return await self.db.get_body_id(div.text)

    async def _parse_gen(self, brand, model, glass_id):
        url = f"{cfg.BASE_URL}/{brand}/{model}/{glass_id}?filter=front"
        soup = await self._get_page(url)

        if 'не найден' in soup.text:
            height, width = None, None

        else:
            info = soup.find("div", {"class": "tech-info"})
            try:
                params = info.find_all("div", {"class": "df-box"})
                params = [[x.text.strip().lower() for x in p.find_all("div")] for p in params]
                # этой строчкой делим дивы внутри этого контейнера на пары и берем текст
                params = {k.split(" ")[0]: int(v) for k, v in params if "(мм)" in k}
                # отфильтруем пары которые не содержат миллиметров в имени
                height, width = params["высота"], params["ширина"]
            except:
                height, width = await self.parse_second_front(info)

        return glass_id, height, width

    async def parse_second_front(self, info):
        res = []
        try:
            for i in info.text.strip().split():
                if i.isdigit():
                    if len(i) >= 3:
                        res.append(i)
            return res[0], res[1]

        except:
            return None, None
