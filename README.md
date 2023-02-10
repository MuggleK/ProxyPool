# ProxyPool

![](https://img.shields.io/badge/python-3.7%2B-brightgreen)

简易高效的代理池，提供如下功能：

- 定时抓取免费代理网站，简易可扩展。
- 使用 Redis 对代理进行存储并对代理可用性进行排序。
- 超时检测，定时筛选，剔除不可用代理，留下可用代理。
- 提供代理 API，随机取用测试通过的可用代理。

本项目参考「[如何搭建一个高效的代理池](https://cuiqingcai.com/7048.html)」，建议使用之前阅读。

### 使用Docker构建接口服务镜像&容器

yml可配置项
```shell
environment:
  APP_ENV: PROD
  API_PORT: 5633
  REDIS_HOST: 127.0.0.1
  REDIS_PORT: 6379
  ...
```

docker-compose 启动
```shell script
docker-compose build

docker-compose up
```

运行结果类似如下：

```
redis        | 1:M 19 Feb 2020 17:09:43.940 * DB loaded from disk: 0.000 seconds
redis        | 1:M 19 Feb 2020 17:09:43.940 * Ready to accept connections
proxypool    | 2020-02-19 17:09:44,200 CRIT Supervisor is running as root.  Privileges were not dropped because no user is specified in the config file.  If you intend to run as root, you can set user=root in the config file to avoid this message.
proxypool    | 2020-02-19 17:09:44,203 INFO supervisord started with pid 1
proxypool    | 2020-02-19 17:09:45,209 INFO spawned: 'getter' with pid 10
proxypool    | 2020-02-19 17:09:45,212 INFO spawned: 'server' with pid 11
proxypool    | 2020-02-19 17:09:45,216 INFO spawned: 'tester' with pid 12
proxypool    | 2020-02-19 17:09:46,596 INFO success: getter entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
proxypool    | 2020-02-19 17:09:46,596 INFO success: server entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
proxypool    | 2020-02-19 17:09:46,596 INFO success: tester entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
```

访问 [http://localhost:5633/random](http://localhost:5633/random) 即可获取一个随机可用代理。

自定义容器：

```
docker-compose -f build.yaml up
```

### 常规方式

常规方式要求有 Python 和 Redis 环境，具体要求如下：

- Python>=3.7
- Redis：默认本地已搭建好redis或有可远程链接

#### 配置 Redis

设置 Redis 的环境变量有两种方式，一种是分别设置 host、port、password，另一种是设置连接字符串，设置方法分别如下：

设置 host、port、password，如果 password 为空可以设置为空字符串，示例如下：

```shell script
export PROXYPOOL_REDIS_HOST='localhost'
export PROXYPOOL_REDIS_PORT=6379
export PROXYPOOL_REDIS_PASSWORD=''
export PROXYPOOL_REDIS_DB=0
```

或者只设置连接字符串：

```shell script
export PROXYPOOL_REDIS_CONNECTION_STRING='redis://localhost'
```

这里连接字符串的格式需要符合 `redis://[:password@]host[:port][/database]` 的格式，
中括号参数可以省略，port 默认是 6379，database 默认是 0，密码默认为空。

以上两种设置任选其一即可。

#### 安装依赖包

```shell script
pip3 install -r requirements.txt
```

#### 运行代理池

Tester、Getter、Server 全部运行，命令如下：

```shell script
python3 run.py
```

按需分别运行，命令如下：

```shell script
python3 run.py --processor getter
python3 run.py --processor tester
python3 run.py --processor server
```

## 接口说明
```shell
/random # 从总池中随机获取代理
/all # 返回全部代理
/count # 返回总池代理个数
/type # 获取当前池内代理厂商
/type?name=*** # 随机获取***厂商代理
```

## 可配置项说明

### 开关

- ENABLE_TESTER：允许 Tester 启动，默认 true
- ENABLE_GETTER：允许 Getter 启动，默认 true
- ENABLE_SERVER：运行 Server 启动，默认 true

### 环境

- APP_ENV：运行环境，可以设置 dev、test、prod，即开发、测试、生产环境，默认 dev
- APP_DEBUG：调试模式，可以设置 true 或 false，默认 true
- APP_PROD_METHOD: 正式环境启动应用方式，默认是`gevent`，
  可选：`tornado`，`meinheld`（分别需要安装 tornado 或 meinheld 模块）

### Redis 连接

- PROXYPOOL_REDIS_HOST / REDIS_HOST：Redis 的 Host，其中 PROXYPOOL_REDIS_HOST 会覆盖 REDIS_HOST 的值。
- PROXYPOOL_REDIS_PORT / REDIS_PORT：Redis 的端口，其中 PROXYPOOL_REDIS_PORT 会覆盖 REDIS_PORT 的值。
- PROXYPOOL_REDIS_PASSWORD / REDIS_PASSWORD：Redis 的密码，其中 PROXYPOOL_REDIS_PASSWORD 会覆盖 REDIS_PASSWORD 的值。
- PROXYPOOL_REDIS_DB / REDIS_DB：Redis 的数据库索引，如 0、1，其中 PROXYPOOL_REDIS_DB 会覆盖 REDIS_DB 的值。
- PROXYPOOL_REDIS_CONNECTION_STRING / REDIS_CONNECTION_STRING：Redis 连接字符串，其中 PROXYPOOL_REDIS_CONNECTION_STRING 会覆盖 REDIS_CONNECTION_STRING 的值。
- PROXYPOOL_REDIS_KEY / REDIS_KEY：Redis 储存代理使用字典的名称，其中 PROXYPOOL_REDIS_KEY 会覆盖 REDIS_KEY 的值。

### 处理器

- CYCLE_TESTER：Tester 运行周期，即间隔多久运行一次测试，默认 5 秒
- CYCLE_GETTER：Getter 运行周期，即间隔多久运行一次代理获取，默认 10 秒
- TEST_URL：测试 URL，默认百度
- TEST_TIMEOUT：测试超时时间，默认 5 秒
- TEST_BATCH：批量测试数量，WIN环境最大500个，Linux最大1000个
- TEST_VALID_STATUS：测试有效的状态码
- EXPIRE_TIMES：IP超时时间
- API_HOST：代理 Server 运行 Host，默认 0.0.0.0
- API_PORT：代理 Server 运行端口，默认 5633
- API_THREADED：代理 Server 是否使用多线程，默认 true

### 日志

- LOG_DIR：日志相对路径
- LOG_RUNTIME_FILE：运行日志文件名称
- LOG_ERROR_FILE：错误日志文件名称
- LOG_ROTATION: 日志记录周转周期或大小，默认 500MB，见 [loguru - rotation](https://github.com/Delgan/loguru#easier-file-logging-with-rotation--retention--compression)
- LOG_RETENTION: 日志保留日期，默认 7 天，见 [loguru - retention](https://github.com/Delgan/loguru#easier-file-logging-with-rotation--retention--compression)
- ENABLE_LOG_FILE：是否输出 log 文件，默认 true，如果设置为 false，那么 ENABLE_LOG_RUNTIME_FILE 和 ENABLE_LOG_ERROR_FILE 都不会生效
- ENABLE_LOG_RUNTIME_FILE：是否输出 runtime log 文件，默认 true
- ENABLE_LOG_ERROR_FILE：是否输出 error log 文件，默认 true

以上内容均可使用环境变量配置，即在运行前设置对应环境变量值即可，如更改测试地址和 Redis 键名：

```shell script
export TEST_URL=http://weibo.cn
export REDIS_KEY=proxies:weibo
```

即可构建一个专属于微博的代理池，有效的代理都是可以爬取微博的。

如果使用 Docker-Compose 启动代理池，则需要在 docker-compose.yml 文件里面指定环境变量，如：

```yaml
version: "3"
services:
  redis:
    image: redis:alpine
    container_name: redis
    command: redis-server
    ports:
      - "6379:6379"
    restart: always
  proxypool:
    build: .
    image: "germey/proxypool"
    container_name: proxypool
    ports:
      - "5633:5633"
    restart: always
    environment:
      REDIS_HOST: redis
      TEST_URL: http://weibo.cn
      REDIS_KEY: proxies:weibo
```

## 扩展代理爬虫

代理的爬虫均放置在 proxypool/crawlers 文件夹下，目前对接了有限几个代理的爬虫。

若扩展一个爬虫，只需要在 crawlers 文件夹下新建一个 Python 文件声明一个 Class 即可。

写法规范如下：

```python
from pyquery import PyQuery as pq
from proxypool.schemas.proxy import Proxy
from proxypool.crawlers.base import BaseCrawler

BASE_URL = 'http://www.664ip.cn/{page}.html'
MAX_PAGE = 5

class Daili66Crawler(BaseCrawler):
    """
    daili66 crawler, http://www.66ip.cn/1.html
    """
    urls = [BASE_URL.format(page=page) for page in range(1, MAX_PAGE + 1)]

    def parse(self, html):
        """
        parse html file to get proxies
        :return:
        """
        doc = pq(html)
        trs = doc('.containerbox table tr:gt(0)').items()
        for tr in trs:
            host = tr.find('td:nth-child(1)').text()
            port = int(tr.find('td:nth-child(2)').text())
            yield Proxy(host=host, port=port)
```

在这里只需要定义一个 Crawler 继承 BaseCrawler 即可，然后定义好 urls 变量和 parse 方法即可。

- urls 变量即为爬取的代理网站网址列表，可以用程序定义也可写成固定内容。
- parse 方法接收一个参数即 html，代理网址的 html，在 parse 方法里只需要写好 html 的解析，解析出 host 和 port，并构建 Proxy 对象 yield 返回即可。

网页的爬取不需要实现，BaseCrawler 已经有了默认实现，如需更改爬取方式，重写 crawl 方法即可。

欢迎大家多多发 Pull Request 贡献 Crawler，使其代理源更丰富强大起来。

## 部署

本项目提供了 Kubernetes 部署脚本，如需部署到 Kubernetes，请参考 [kubernetes](./kubernetes)。

## 可视化

- [ ] Grafana配合MySQL 监控IP使用情况
