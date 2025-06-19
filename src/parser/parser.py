import asyncio
import random

from aiohttp import ClientSession, ClientTimeout, ClientError
from aiohttp_proxy import ProxyType, ProxyConnector
from bs4 import BeautifulSoup

from config import cfg
from utils import dict_to_json


TIMEOUT = ClientTimeout(total=cfg.proxy_check_timeout)


class MainParser:

    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()

    async def run(self):
        print(cfg.proxy_user)
        proxy_type = ProxyType.HTTP if cfg.scheme == "http" else ProxyType.HTTPS
        kwargs = {
            "timeout": TIMEOUT,
            "connector": ProxyConnector(
                proxy_type=proxy_type,
                username=cfg.proxy_user,
                password=cfg.proxy_pass,
                host=cfg.proxy_host,
                port=cfg.proxy_port,
            )
        }
        async with ClientSession(**kwargs) as self.session:
            await self.get_pages()

    async def get_pages(self):
        home = await self.get_page(cfg.HOME_URL)
        home_page = await self.get_home_page(home)

        tasks_brands = [self.get_all_brand_links(brand) for brand in home_page]
        brands = await asyncio.gather(*tasks_brands)

        tasks_models = [self.get_models(model) for model in brands]
        models = await  asyncio.gather(*tasks_models)

        task_gens = [self.get_gen(model) for model in models]
        gens = await asyncio.gather(*task_gens)

        task_glasses = [self.get_glass(gen) for gen in gens]
        glasses = await asyncio.gather(*task_glasses)

        task_info = [self.get_info(size) for size in glasses]
        info = await asyncio.gather(*task_info)

        print(self.data)
        dict_to_json(self.data)

    async def get_page(self, url):
        retries = cfg.request_attempts
        for attempt in range(retries):
            try:
                async with self.session.get(url, headers=cfg.headers) as response:

                    if response.status == 429:
                        print(f'Status code {response.status}. Too many requests. Wait...')
                        await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                        continue

                    elif response.status != 200:
                        print(f"Website is DOWN! Status code {response.status}")
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

    async def _update_data(self, brand, model, gen, size):
        async with self.lock:
            if brand not in self.data:
                self.data[brand] = {}
            if model not in self.data[brand]:
                self.data[brand][model] = {}
            if gen not in self.data[brand][model]:
                self.data[brand][model][gen] = {}

            self.data[brand][model][gen] = size


    async def get_home_page(self, page):
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        return data

    async def get_all_brand_links(self, brand_link):
        link = brand_link['href'].split('/', 2)
        url = cfg.HOME_URL.rstrip('/') + '/' + cfg.CITY + '/' + link[2]
        return url

    async def get_models(self, brand):
        models_list = []
        models = await self.get_page(brand)
        soup = BeautifulSoup(models, "html.parser")
        container = soup.find("div", class_="marks")
        models = container.find_all('a', href=True)
        for i in models:
            link = i['href'].split('/', 3)
            url = cfg.HOME_URL.rstrip('/') + '/' + cfg.CITY + '/steklo/' + link[3]
            models_list.append(url)

        return models_list

    async def get_gen(self, models):
        all_gens = []
        for i in models:
            gen = await self.get_page(i)

            try:
                soup = BeautifulSoup(gen, "html.parser")
                container = soup.find("section", class_="gen-list")
                gens = container.find_all('a', href= True)
                for i in gens:
                    link = i['href'].split('/', 3)
                    url = cfg.HOME_URL.rstrip('/') + '/' + cfg.CITY + '/glass-types/' + link[3]
                    all_gens.append(url)

            except Exception as e:
                print(f'{e}. BS4 received {gen}')

        return all_gens

    async def get_glass(self, gens):
        result = []
        for i in gens:
            glass = await self.get_page(i)

            try:
                soup = BeautifulSoup(glass, "html.parser")
                container = soup.find("section", class_="glass-type")
                windshield = container.find('a')
                link = windshield['href'].split('/', 3)
                url = cfg.HOME_URL.rstrip('/') + '/' + cfg.CITY + '/steklo/' + link[3]
                result.append(url)

            except Exception as e:
                print(f'{e}. BS4 received {glass} ')

        return result

    async def get_info(self, glasses):
        for i in glasses:
            glass = await self.get_page(i)

            try:
                soup = BeautifulSoup(glass, "html.parser")
                link = i.split('/')
                brand, model = link[5], link[6]
                gen = soup.find('strong')

                if 'не найден' in soup.text:
                    await self._update_data(brand, model, gen.text, "Товар не найден")

                else:
                    sizes = []
                    glass_info = soup.find_all("div", class_="dropdown-block")
                    for i in glass_info:
                        result = i.text.strip().split()
                        for size in result:
                            if size.isdigit():
                                sizes.append(size)

                    await self._update_data(brand, model, gen.text, str(sizes[:2]))

            except Exception as e:
                print(f'{e}. BS4 received {glass}')