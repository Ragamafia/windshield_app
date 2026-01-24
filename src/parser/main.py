import asyncio
import random

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from config import cfg


class MainParser:
    session: ClientSession

    @staticmethod
    async def new_session():
        timeout = ClientTimeout(total=cfg.proxy_check_timeout)
        return ClientSession(connector=None, timeout=timeout, headers=cfg.headers)

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
                print(f"{response.status}: Too Many Requests")
                await asyncio.sleep(random.randint(5, 15))
            elif response.status == 403:
                print(f"{response.status}: Forbidden")
                await asyncio.sleep(random.randint(18, 25))
            elif response.status == 404:
                print(f"{response.status}: Website is DOWN!")
                return
            else:
                print(f"Response: {response.status}")
            attempts -= 1
            if attempts:
                return await self.request(method, url, attempts, **kwargs)

    async def _get_page(self, url: str):
        page = await self.get(url)
        try:
            if soup := BeautifulSoup(page, "html.parser"):
                    return soup
        except:
            await asyncio.sleep(random.randint(20, 25))
            print(f"RETRY GET: {url}")
            await self._get_page(url)
