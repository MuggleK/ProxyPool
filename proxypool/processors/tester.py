import asyncio

import httpx
from loguru import logger
from proxypool.schemas import Proxy
from proxypool.storages.redis import RedisClient
from proxypool.setting import TEST_TIMEOUT, TEST_BATCH, TEST_URL, TEST_VALID_STATUS, TEST_ANONYMOUS, ORIGIN_URL, REDIS_KEY
from proxypool.crawlers import __all__ as crawlers_cls
from asyncio import TimeoutError
from httpx import ReadTimeout, ConnectTimeout, ProxyError, RemoteProtocolError, ConnectError, ReadError
from json import JSONDecodeError


EXCEPTIONS = (
    JSONDecodeError,
    ConnectionRefusedError,
    TimeoutError,
    AssertionError,
    ReadTimeout,
    ConnectTimeout,
    ProxyError,
    RemoteProtocolError,
    ConnectError,
    ReadError
)


class Tester(object):
    """
    tester for testing proxies in queue
    """
    
    def __init__(self):
        """
        init redis
        """
        self.redis = RedisClient()
        self.loop = asyncio.get_event_loop()
    
    async def test(self, redis_key, proxy: Proxy):
        """
        test single proxy
        :param proxy: Proxy object
        :return:
        """
        async with httpx.AsyncClient(proxies=f'http://{proxy.string()}', timeout=TEST_TIMEOUT,
                                     follow_redirects=False) as session:
            try:
                # if TEST_ANONYMOUS is True, make sure that
                # the proxy has the effect of hiding the real IP
                if TEST_ANONYMOUS:
                    url = 'http://httpbin.org/ip'
                    response = await session.get(url)
                    if response.status_code not in TEST_VALID_STATUS:
                        self.redis.remove(redis_key, proxy)
                        return
                    resp_json = response.json()
                    anonymous_ip = resp_json.get('origin')
                    assert ORIGIN_URL != anonymous_ip
                response = await session.get(TEST_URL)
                if response.status_code not in TEST_VALID_STATUS:
                    self.redis.remove(redis_key, proxy)
            except EXCEPTIONS:
                self.redis.remove(redis_key, proxy)
    
    @logger.catch
    def run(self):
        """
        test main method
        :return:
        """
        # event loop of aiohttp
        logger.info('stating tester...')
        for crawler in crawlers_cls:
            redis_key = f"{REDIS_KEY}:{crawler.__name__}"
            self.redis.remove_expire(redis_key)
            cursor = 0
            while True:
                logger.debug(f'testing {crawler.__name__} use cursor {cursor}, count {TEST_BATCH}')
                cursor, proxies = self.redis.batch(redis_key, cursor, count=TEST_BATCH)
                if proxies:
                    tasks = [self.test(redis_key, proxy) for proxy in proxies]
                    self.loop.run_until_complete(asyncio.wait(tasks))
                if not cursor:
                    break


def run_tester():
    host = '96.113.165.182'
    port = '3128'
    tasks = [tester.test(f"{REDIS_KEY}:TEST", Proxy(host=host, port=port))]
    tester.loop.run_until_complete(asyncio.wait(tasks))


if __name__ == '__main__':
    tester = Tester()
    tester.run()
    # run_tester()

