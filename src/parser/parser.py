import asyncio
import random

from aiohttp import ClientSession, ClientTimeout, ClientError
from aiohttp_proxy import ProxyConnector
from bs4 import BeautifulSoup

from utils import save_image, process_gen
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
        proxy = f"{cfg.scheme}://{cfg.proxy_user}:{cfg.proxy_pass}@{cfg.proxy_host}:{cfg.proxy_port}"
        connector = ProxyConnector.from_url(proxy)
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

                elif model := await self.get_model_to_parse():
                    brand, model_name = model
                    if result := await self._parse_model(brand, model_name):
                        task = [db.put_gens(**res) for res in result]
                        await asyncio.gather(*task)

                else:
                    self.started = False

                #     brand, model, glass_id = gen
                #     if size := await self._parse_gen(brand, model, glass_id):
                #         height, width = size
                #         await db.put_size(height, width)



    async def request(self, url):
        for attempt in range(cfg.request_attempts):
            try:
                async with self.session.get(url) as response:

                    if response.status == 429:
                        print(f'Status code {response.status}. Too many requests. Wait...')
                        await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                        continue

                    elif response.status != 200:
                        print(f'Status code {response.status}.')
                        exit()

                    elif response.status == 200:
                        try:
                            page = await response.text()
                            if page is not None:
                                return page

                        except Exception as e:
                            print(f'{e}. Response is {page}.')

            except ClientError as e:
                print(f"ERROR: {e}")


    async def get_image(self, url):
        try:
            async with self.session.get(url) as response:

                if response.status != 200:
                    print(f'Error get image: Response status {response.status}')
                    exit()

                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    print('No image')
                if image := await response.read():
                    return image

        except Exception as e:
            print(f"Error get image. Response status {response.status}. {e}")


    async def get_model_to_parse(self):
        try:
            brand, model = await db.get_model()
            return brand, model
        except:
            gens = await db.get_gen()
            logger.success(f"Added {gens} cars.")


    async def get_gen_to_parse(self):
        ...

    async def _parse_all_brands(self):
        brands = []
        home = await self.request(cfg.HOME_URL)
        soup = BeautifulSoup(home, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        for i in data:
            link = i['href'].split('/', 3)
            brands.append(link[3])

        return brands

    async def _parse_brand(self, brand) -> list:
        url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/steklo/{brand}"
        models = []

        page = await self.request(url)
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)

        for i in data:
            link = i['href'].split('/', 4)
            models.append(link[4])

        return models

    async def _parse_model(self, brand, model) -> list[dict]:
        url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/steklo/{brand}/{model}"
        page = await self.request(url)
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find("section", class_="gen-list")
        years = container.find_all('div', class_='years')
        gens = container.find_all('div', class_='gens')
        links = container.find_all('a', href=True)
        ids = [l['href'].split('/', 5)[5] for l in links]

        results = []
        for i, y, g in zip(ids, years, gens):
            year_start, year_end, gen, restyle = process_gen(y, g)
            print(year_start, year_end, gen, restyle)

            results.append({
                "brand": brand,
                "model": model,
                "glass_id": i,
                "year_start": year_start,
                "year_end": year_end,
                "gen": gen,
                "restyle": restyle,
            })

        return results

        # image = i.find('img', src=True)
        # img = await self.get_image(image['src'])
        # save_dir = cfg.path_to_images / brand / model / gen
        # save_image(save_dir, img)

    async def _parse_gen(self, brand, model, glass_id):
        url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/steklo/{brand}/{model}/{glass_id}?filter=font"

        page = await self.request(url)
        soup = BeautifulSoup(page, "html.parser")

        if 'не найден' in soup.text:
            logger.warning(f'No size for: {brand} {model} {glass_id}')
            return

        else:
            sizes = []
            glass_info = soup.find_all("div", class_="dropdown-block")
            for i in glass_info:
                result = i.text.strip().split()
                for size in result:
                    if size.isdigit():
                        sizes.append(size)

            logger.info(f'Added size: {brand} {model} {glass_id}')
            return str(sizes[0]), str(sizes[1])
