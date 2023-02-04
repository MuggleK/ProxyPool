import redis
from proxypool.exceptions import PoolEmptyException
from proxypool.schemas.proxy import Proxy
from proxypool.setting import REDIS_CONNECTION_STRING, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, REDIS_KEY, PROXY_SCORE_MAX, PROXY_SCORE_MIN, \
    PROXY_SCORE_INIT
from random import choice
from typing import List
from loguru import logger
from proxypool.utils.proxy import is_valid_proxy, convert_proxy_or_proxies


REDIS_CLIENT_VERSION = redis.__version__
IS_REDIS_VERSION_2 = REDIS_CLIENT_VERSION.startswith('2.')


class RedisClient(object):
    """
    redis connection client of proxypool
    """

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB,
                 connection_string=REDIS_CONNECTION_STRING, **kwargs):
        """
        init redis client
        :param host: redis host
        :param port: redis port
        :param password: redis password
        :param connection_string: redis connection_string
        """
        # if set connection_string, just use it
        if connection_string:
            self.db = redis.StrictRedis.from_url(connection_string, decode_responses=True, **kwargs)
        else:
            self.db = redis.StrictRedis(
                host=host, port=port, password=password, db=db, decode_responses=True, **kwargs)

    def add(self, redis_key, proxy: Proxy, score=PROXY_SCORE_INIT) -> int:
        """
        add proxy and set it to init score
        :param redis_key:
        :param proxy: proxy, ip:port, like 8.8.8.8:88
        :param score: int score
        :return: result
        """
        if not is_valid_proxy(f'{proxy.host}:{proxy.port}'):
            logger.info(f'invalid proxy {proxy}, throw it')
            return
        if not self.exists(redis_key, proxy):
            if IS_REDIS_VERSION_2:
                return self.db.zadd(redis_key, score, proxy.string())
            return self.db.zadd(redis_key, {proxy.string(): score})

    def random(self, redis_key=None) -> Proxy:
        """
        get random proxy
        firstly try to get proxy with max score
        if not exists, try to get proxy by rank
        if not exists, raise error
        :param redis_key:
        :return: proxy, like 8.8.8.8:8
        """
        keys = [redis_key] if redis_key else self.keys()
        # try to get proxy with max score
        max_proxies = list()
        for redis_key in keys:
            proxies = self.db.zrangebyscore(redis_key, PROXY_SCORE_MAX, PROXY_SCORE_MAX)
            max_proxies.extend(proxies)
        if len(max_proxies):
            return convert_proxy_or_proxies(choice(max_proxies))
        # else get proxy by rank
        all_proxy = self.all()
        if len(all_proxy):
            return choice(all_proxy)
        # else raise error
        raise PoolEmptyException

    def remove(self, redis_key, proxy: Proxy) -> int:
        """
        if proxy is useless, remove it
        :param redis_key:
        :param proxy: proxy
        :return: new score
        """
        # if IS_REDIS_VERSION_2:
        #     self.db.zincrby(REDIS_KEY, proxy.string(), -1)
        # else:
        #     self.db.zincrby(REDIS_KEY, -1, proxy.string())
        logger.debug(f'{proxy.string()} is useless, remove')
        self.db.zrem(redis_key, proxy.string())

    def exists(self, redis_key, proxy: Proxy) -> bool:
        """
        if proxy exists
        :param redis_key:
        :param proxy: proxy
        :return: if exists, bool
        """
        return not self.db.zscore(redis_key, proxy.string()) is None

    def max(self, redis_key, proxy: Proxy) -> int:
        """
        set proxy to max score
        :param redis_key:
        :param proxy: proxy
        :return: new score
        """
        logger.info(f'{proxy.string()} is valid, set to {PROXY_SCORE_MAX}')
        if IS_REDIS_VERSION_2:
            return self.db.zadd(redis_key, PROXY_SCORE_MAX, proxy.string())
        return self.db.zadd(redis_key, {proxy.string(): PROXY_SCORE_MAX})

    def count(self) -> int:
        """
        get count of proxies
        :return: count, int
        """
        counts = 0
        for redis_key in self.keys():
            counts += self.db.zcard(redis_key)
        return counts

    def all(self) -> List[Proxy]:
        """
        get all proxies
        :return: list of proxies
        """
        proxy_list = list()
        for redis_key in self.keys():
            proxies = convert_proxy_or_proxies(self.db.zrangebyscore(redis_key, PROXY_SCORE_MIN, PROXY_SCORE_MAX))
            proxy_list.extend(proxies)
        return proxy_list

    def batch(self, redis_key, cursor, count) -> List[Proxy]:
        """
        get batch of proxies
        :param redis_key:
        :param cursor: scan cursor
        :param count: scan count
        :return: list of proxies
        """
        cursor, proxies = self.db.zscan(redis_key, cursor, count=count)
        return cursor, convert_proxy_or_proxies([i[0] for i in proxies])

    def keys(self):
        return self.db.keys()

    def crawler_type(self):
        redis_key = self.keys()
        types = [key.split(":")[-1].strip("Crawler") for key in redis_key]
        return ' '.join(types)

    def get_special(self, name):
        redis_key = f"proxies:{name}Crawler"
        return self.random(redis_key).string()


if __name__ == '__main__':
    conn = RedisClient()
    result = conn.keys()
    print(result)
