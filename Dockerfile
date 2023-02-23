FROM python:3.11.2-slim-buster

WORKDIR /src

RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    apt clean && \
    rm -rf /var/cache/apt/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

COPY ./requirements /src/requirements

RUN pip install -U pip && \
    pip install --no-cache-dir -r /src/requirements/local.txt

COPY . /src
ENV PATH "$PATH:/src/scripts"


CMD ["./scripts/start-dev-tests.sh"]
