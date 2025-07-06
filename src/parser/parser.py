import asyncio
import random

from aiohttp import ClientSession, ClientTimeout
from aiohttp_proxy import ProxyConnector
from bs4 import BeautifulSoup

from db.ctrl import db
from config import cfg
from logger import logger

BASE_URL: str = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/steklo"


class MainParser:
    session: ClientSession

    def __init__(self):
        self.started = True

    @staticmethod
    async def new_session():
        timeout = ClientTimeout(total=cfg.proxy_check_timeout)
        proxy = (f"{cfg.scheme}://{cfg.proxy_user}:{cfg.proxy_pass}@"
                 f"{cfg.proxy_host}:{cfg.proxy_port}")
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

                elif model := await db.get_model_to_parse():
                    if result := await self._parse_model(*model):
                        task = [db.put_gens(**res) for res in result]
                        await asyncio.gather(*task)

                else:
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

    async def _parse_all_brands(self):
        home = await self.get(cfg.HOME_URL)
        soup = BeautifulSoup(home, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        brands = [i['href'].split('/', 3)[3] for i in data]
        return brands

    async def _parse_brand(self, brand) -> list:
        page = await self.get(f"{BASE_URL}/{brand}")
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        models = [i['href'].split('/', 4)[4] for i in data]
        return models

    async def _parse_model(self, brand, model) -> list[dict]:
        results = []
        page = await self.get(f"{BASE_URL}/{brand}/{model}")
        soup = BeautifulSoup(page, "html.parser")
        cards = soup.find_all("div", {"class": "group-car-card"})
        for card in soup.find_all("div", {"class": "group-car-card"}):
            try:
                results.append({
                    "glass_id": card.find("a")["href"].split("/")[-1],
                    "brand": brand,
                    "model": model,
                    **self._parse_years(card),
                    **self._parse_generation(card),
                })
            except Exception as e:
                print(f"Can not parse generation for {brand} {model}: "
                      f"'{e}'\n{card}")
        if not results:
            print(f"   +++ SOSNOOLEY {cards=}")
        return results


    def _parse_years(self, card):
        if div := card.find("div", {"class": "caption-year"}):
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

        raise ValueError("Can not parse years")

    def _parse_generation(self, card):
        if span := card.find("span", {"class": "caption-generation"}):
            gen = span.text
            if restyle := "рестайлинг" in span.text:
                gen = span.text.split(",&nbsp")[0]
            gen = gen.replace("Поколение", "")
            try:
                return {"gen": int(gen.strip()), "restyle": restyle}
            except:
                ...

        raise ValueError("Can not parse generation")

    async def _parse_gen(self, brand, model, glass_id):
        url = f"{BASE_URL}/{brand}/{model}/{glass_id}?filter=font"
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
