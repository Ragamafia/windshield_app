import asyncio
import random
import re

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from config import cfg


class MainParser:
    session: ClientSession

    def __init__(self):
        self.started = True

    @staticmethod
    async def new_session():
        timeout = ClientTimeout(total=cfg.proxy_check_timeout)
        return ClientSession(connector=None, timeout=timeout, headers=cfg.headers)

    async def run(self):
        async with await self.new_session() as self.session:
            if result := await self._parse_model("toyota", "corolla"):
                for i in result:
                    print(i)

            else:
                print("DONE")

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

    async def _parse_model(self, brand, model) -> list[dict]:
        page = await self.get(f"{cfg.BASE_URL}/{brand}/{model}")
        try:
            soup = BeautifulSoup(page, "html.parser")
        except TypeError as e:
            print(f'ERROR! {e}')
            return

        results = []

        if cards := soup.find_all("div", {"class": "group-car-card"}):
            for card in cards:
                groups = card.find_all("div", {"class": "car-group"})
                for group in groups:
                    cars = group.find_all("a", {"class": "car-card"})
                    for car in cars:
                        data = {
                            "brand": brand,
                            "model": model,
                            "glass_id": self._parse_glass_id(car),
                            **self._parse_years(card),
                            **self._parse_generation(card),
                            "body": self._parse_body(car),
                        }
                        results.append(data)
        else:
            cards = soup.find_all("div", {"class": "car-info"})
            for card in cards:
                results.append(self.get_data(brand, model, card))

        return results

    def get_data(self, brand, model, card):
        try:
            return {
                "brand": brand,
                "model": model,
                "glass_id": self._parse_glass_id(card),
                **self._parse_years(card),
                **self._parse_generation(card),
                "body": self._parse_body(card),
            }

        except Exception as e:
            print(f"Can not parse generation for {brand} {model}:\n "
                  f"{e}\n{card}")

    def _parse_glass_id(self, card):
        try:
            id = card["href"].split("/")[-1]
        except:
            id = card.parent.parent["href"].split("/")[-1]
        return id

    def _parse_body(self, card):
        div = card.find("div", class_=["name"])
        if not div:
            div = card.find("div", class_=["serie"])
        return div.text

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


if __name__ == "__main__":
    parser = MainParser()
    asyncio.run(parser.run())
