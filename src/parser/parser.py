import asyncio
import random

from aiohttp import ClientSession, ClientTimeout, ClientError
from aiohttp_proxy import ProxyConnector
from bs4 import BeautifulSoup

from utils import save_image, process_gen
from db.cars import car
from config import cfg
from logger import logger

class MainParser:

    async def run(self):
        timeout = ClientTimeout(total=cfg.proxy_check_timeout)
        proxy = f"{cfg.scheme}://{cfg.proxy_user}:{cfg.proxy_pass}@{cfg.proxy_host}:{cfg.proxy_port}"
        connector = ProxyConnector.from_url(proxy)

        async with ClientSession(connector=None, timeout=timeout, headers=cfg.headers) as self.session:
            await self.get_pages()

    async def get_pages(self):
        home = await self.request(cfg.HOME_URL)
        home_page = await self.get_home_page(home)

        tasks_brands = [self.get_brand_links(brand) for brand in home_page]
        brands = await asyncio.gather(*tasks_brands)

        tasks_models = [self.get_models(model) for model in brands]
        models = await  asyncio.gather(*tasks_models)

        task_gens = [self.get_gen_and_image(model) for model in models]
        gens = await asyncio.gather(*task_gens)

        task_glasses = [self.get_glass_link(gen) for gen in gens]
        glasses = await asyncio.gather(*task_glasses)

        task_info = [self.get_info(size) for size in glasses]
        info = await asyncio.gather(*task_info)

    async def request(self, url):
        for attempt in range(cfg.request_attempts):
            try:
                async with self.session.get(url) as response:

                    if response.status == 429:
                        print(f'Status code {response.status}. Too many requests. Wait...')
                        await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                        continue

                    elif response.status != 200:
                        print(f'Status code {response.status}. BAN!')
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


    async def get_home_page(self, page):
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find("div", class_="marks")
        data = container.find_all('a', href=True)
        return data

    async def get_brand_links(self, brand_link):
        link = brand_link['href'].split('/', 2)
        url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/{link[2]}"
        brand = link[2].split('/')

        await car.put_brand(brand[1])

        return url

    async def get_models(self, brand):
        models_list = []
        models = await self.request(brand)
        soup = BeautifulSoup(models, "html.parser")
        container = soup.find("div", class_="marks")
        models = container.find_all('a', href=True)

        for i in models:
            link = i['href'].split('/', 3)
            url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/steklo/{link[3]}"
            models_list.append(url)
            mark, model = link[3].split('/')

            await car.put_model(mark, model)

        return models_list

    async def get_gen_and_image(self, models):
        semaphore = asyncio.Semaphore(cfg.semaphore_range)
        all_gens = []

        async with semaphore:
            for i in models:
                try:
                    gen = await self.request(i)
                    soup = BeautifulSoup(gen, "html.parser")
                    container = soup.find("section", class_="gen-list")
                    card = container.find_all('div', class_="group-car-card")

                    for i in card:
                        tag = i.find('a', href=True)
                        link = tag['href'].split('/', 3)
                        url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/glass-types/{link[3]}"
                        all_gens.append(url)

                        brand, model, gen_id = link[3].split('/')
                        years = i.find('span', class_='text')
                        gen = i.find('span', class_='caption-generation')
                        self.year_start, self.year_end, self.gen, self.restyle = process_gen(years.text, gen.text)

                        await car.put_gen(brand, model, self.year_start, self.year_end, self.gen, self.restyle)

                        # image = i.find('img', src=True)
                        # brand, model, gen = link[3].split('/')
                        #
                        # img = await self.get_image(image['src'])
                        # save_dir = cfg.path_to_images / brand / model / gen
                        # save_image(save_dir, img)

                except Exception as e:
                    print(f'Error get gen: {e}')

        return all_gens

    async def get_glass_link(self, gens):
        semaphore = asyncio.Semaphore(cfg.semaphore_range)
        glasses = []

        async with semaphore:
            for i in gens:
                try:
                    glass = await self.request(i)
                    soup = BeautifulSoup(glass, "html.parser")
                    container = soup.find("section", class_="glass-type")
                    windshield = container.find('a')
                    link = windshield['href'].split('/', 3)
                    url = f"{cfg.HOME_URL.rstrip('/')}/{cfg.CITY}/steklo/{link[3]}"
                    glasses.append(url)

                except Exception as e:
                    print(f'Error get glass link: {e}')

        return glasses

    async def get_info(self, glasses):
        semaphore = asyncio.Semaphore(cfg.semaphore_range)
        async with semaphore:
            for i in glasses:
                try:
                    glass = await self.request(i)
                    soup = BeautifulSoup(glass, "html.parser")
                    link = i.split('/')
                    brand, model = link[5], link[6]

                    if 'не найден' in soup.text:
                        #await car.put_gen(brand, model, self.year_start, self.year_end, self.gen, self.restyle)
                        logger.warning(f'No size for: {brand, model, self.year_start}-{self.year_end}')

                    else:
                        sizes = []
                        glass_info = soup.find_all("div", class_="dropdown-block")
                        for i in glass_info:
                            result = i.text.strip().split()
                            for size in result:
                                if size.isdigit():
                                    sizes.append(size)

                        await car.put_gen(height=str(sizes[0]), width=str(sizes[1]))
                        logger.info(f'Added car: {brand} {model} {self.year_start}-{self.year_end}')

                except Exception as e:
                    print(f'Error get info: {e}')