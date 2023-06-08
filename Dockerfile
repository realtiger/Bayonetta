FROM python:3.11-alpine

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app/program"

# copy poetry files and env file
COPY ./pyproject.toml ./poetry.lock ./.env ./docker /app/

# change source
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    # install linux dependencies
    apk update && \
    apk add gcc bash python3-dev musl-dev vim git mariadb-dev nginx libc-dev make libffi-dev openssl-dev libxml2-dev libxslt-dev && \
    # install python dependencies
    pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir poetry -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi && \
    pip install supervisor -i https://pypi.tuna.tsinghua.edu.cn/simple


# copy project
COPY ./program /app/program

EXPOSE 5000 9001

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
