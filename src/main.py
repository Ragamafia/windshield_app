import asyncio
import time

from bot.bot import DetailerBot
from parser.parser import MainParser


def make_parse():
    parser = MainParser()
    start_time = time.time()
    asyncio.run(parser.run())
    end_time = time.time()
    print(f'Parsing done. Times {end_time - start_time} seconds')

async def run_bot():
    bot = DetailerBot()
    await bot.run()


if __name__ == '__main__':
    asyncio.run(run_bot())
