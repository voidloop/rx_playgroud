import asyncio
import json
import logging
import sys

import aiohttp
import rx
from rx import operators as ops
from rx.scheduler.eventloop import AsyncIOScheduler
from rx.subject import Subject

logging.basicConfig(level=logging.DEBUG)


class WikipediaFinder:
    def __init__(self, loop):
        self._loop = loop
        self._url = 'http://en.wikipedia.org/w/api.php'

    async def search(self, term):
        params = {
            "action": 'opensearch',
            "search": term,
            "format": 'json'
        }
        logging.debug('Searching "{}"...'.format(term))
        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.get(self._url, params=params) as resp:
                return await resp.text()


async def main(loop):
    scheduler = AsyncIOScheduler(loop)
    finder = WikipediaFinder(loop)
    stream = Subject()

    def task(term):
        t = loop.create_task(finder.search(term))
        return rx.from_future(t)

    def pretty(result):
        parsed = json.loads(result)
        print(json.dumps(parsed, sort_keys=True, indent=2))

    stream.pipe(
        ops.debounce(0.750),
        ops.distinct(),
        ops.flat_map_latest(task)
    ).subscribe(pretty, scheduler=scheduler)

    def reader():
        line = sys.stdin.readline().strip()
        stream.on_next(line)

    loop.add_reader(sys.stdin.fileno(), reader)


if __name__ == '__main__':
    the_loop = asyncio.get_event_loop()
    try:
        the_loop.create_task(main(the_loop))
        the_loop.run_forever()
    except KeyboardInterrupt:
        logging.debug('Process interrupted.')
