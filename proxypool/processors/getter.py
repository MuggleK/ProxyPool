from loguru import logger
from proxypool.storages.redis import RedisClient
from proxypool.setting import PROXY_NUMBER_MAX, REDIS_KEY, EXPIRE_TIMES
from proxypool.crawlers import __all__ as crawlers_cls


class Getter(object):
    """
    getter of proxypool
    """

    def __init__(self):
        """
        init db and crawlers
        """
        self.redis = RedisClient()
        self.crawlers_cls = crawlers_cls
        self.crawlers = [crawler_cls for crawler_cls in self.crawlers_cls]

    def is_full(self):
        """
        if proxypool if full
        return: bool
        """
        return self.redis.count() >= PROXY_NUMBER_MAX

    @logger.catch
    def run(self):
        """
        run crawlers to get proxy
        :return:
        """
        if self.is_full():
            return
        for crawler in self.crawlers:
            logger.info(f'crawler {crawler} to get proxy')
            for proxy in crawler().crawl():
                self.redis.add(f"{REDIS_KEY}:{crawler.__name__}", proxy)
            if crawler.check_mode.upper() == "EXPIRE":
                self.redis.db.expire(f"{REDIS_KEY}:{crawler.__name__}", EXPIRE_TIMES)


if __name__ == '__main__':
    getter = Getter()
    getter.run()