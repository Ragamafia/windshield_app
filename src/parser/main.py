import time
import asyncio

from parser import MainParser


if __name__ == '__main__':
    parser = MainParser()
    start_time = time.time()

    asyncio.run(parser.run())

    end_time = time.time()
    print(f'Times: {end_time - start_time} seconds')