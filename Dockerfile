FROM python:3.7.3

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN dpkg-reconfigure -f noninteractive tzdata
RUN mkdir -p /data/logs


WORKDIR /app
COPY . /app
RUN pip install --upgrade pip -i https://pypi.douban.com/simple/
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/

ENV PYTHONPATH=/app
