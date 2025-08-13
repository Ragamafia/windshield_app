import asyncio
import random
import re

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from db.ctrl import db
from config import cfg
from logger import logger


class MainParser:
    session: ClientSession

    def __init__(self):
        self.started = True

    @staticmethod
    async def new_session():
        timeout = ClientTimeout(total=cfg.proxy_check_timeout)
        return ClientSession(connector=None, timeout=timeout, headers=cfg.headers)

    async def ensure_brands(self):
        async with await self.new_session() as self.session:
            if await db.no_brands():
                if brands := await self._parse_all_brands():
                    logger.success(f"Parse {len(brands)} brands.")
                    task = [db.put_brands(brand) for brand in brands]
                    await asyncio.gather(*task)

                else:
                    raise RuntimeError("Can not get all brands. Aborting...")

    async def run(self):
        async with await self.new_session() as self.session:
            while self.started:
                if brand := await db.get_brand_to_parse():
                    if models := await self._parse_brand(brand):
                        task = [db.put_model(brand, model) for model in models]
                        await asyncio.gather(*task)

                elif model := await db.get_model_to_parse():
                    if result := await self._parse_model(*model):
                        task = [db.put_gen(**res) for res in result]
                        await asyncio.gather(*task)

                elif gen := await db.get_gen_to_parse():
                    await self._download_image(*gen)
                    if result := await self._parse_gen(*gen):
                        await db.put_size(*result)

                else:
                    logger.success(f"Parsing complete. Models: {await db.count_models()}. "
                                   f"Total cars: {await db.count_gen()}.")
                    self.started = False

    async def get(self, url):
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

    async def _download_image(self, brand, model, id):
        page = await self.get(f"{cfg.BASE_URL}/{brand}/{model}/{id}")
        try:
            soup = BeautifulSoup(page, "html.parser")
        except TypeError as e:
            print(f'ERROR! {e}')
            return

        image = soup.find('img', {"class": "fluid"})
        image = await self.get(image['src'])

        save_dir = cfg.path_to_images / brand / model / id
        save_dir.mkdir(parents=True, exist_ok=True)
        image_path = save_dir / "img.jpg"

        with open(image_path, 'wb') as file:
            file.write(image)
            logger.success(f'Save new image: {brand} {model} {id}')

    async def _parse_all_brands(self):
        home = await self.get(cfg.HOME_URL)
        soup = BeautifulSoup(home, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        brands = [i['href'].split('/', 3)[3] for i in data]
        return brands

    async def _parse_brand(self, brand) -> list:
        page = await self.get(f"{cfg.BASE_URL}/{brand}")
        try:
            soup = BeautifulSoup(page, "html.parser")
        except TypeError as e:
            print(f'ERROR! {e}')
            return

        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        models = [i['href'].split('/', 4)[4] for i in data]
        return models

    async def _parse_model(self, brand, model) -> list[dict]:
        page = await self.get(f"{cfg.BASE_URL}/{brand}/{model}")
        try:
            soup = BeautifulSoup(page, "html.parser")
        except TypeError as e:
            print(f'ERROR! {e}')
            return

        results = []
        cards = soup.find_all("div", {"class": "group-car-card"})
        if not cards:
            cards = soup.find_all("div", {"class": "car-info"})

        for card in cards:
            try:
                results.append({
                    "brand": brand,
                    "model": model,
                    "glass_id": self._parse_class_id(card),
                    **self._parse_years(card),
                    **self._parse_generation(card),
                })

            except Exception as e:
                print(f"Can not parse generation for {brand} {model}:\n "
                      f"{e}\n{card}")

        return results

    def _parse_class_id(self, card):
        try:
            id = card.find("a")["href"].split("/")[-1]
        except:
            id = card.parent.parent["href"].split("/")[-1]

        return id

    def _parse_years(self, card):
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

    def _parse_generation(self, card):
        span = card.find("span", {"class": "caption-generation"})
        if not span:
            span = card.find("div", {"class": "gens"})

        if match := re.search(r'(\d+)-й рестайлинг', span.text):
            restyle = int(match.group(1))
        else:
            restyle = 0

        gen = span.text.strip().split(',')
        for i in gen[0].split():
            if i.isdigit():
                gen = int(i)

        return {
            "gen": gen,
            "restyle": restyle
        }


    async def _parse_gen(self, brand, model, glass_id):
        url = f"{cfg.BASE_URL}/{brand}/{model}/{glass_id}?filter=front"

        page = await self.get(url)
        try:
            soup = BeautifulSoup(page, "html.parser")
        except TypeError as e:
            print(f'ERROR! {e}')
            return

        if 'не найден' in soup.text:
            logger.warning(f'No size for: {brand} {model} {glass_id}')
            return None

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