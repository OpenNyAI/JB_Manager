
FROM python:3.11-buster as builder

RUN pip install poetry==1.8.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app
COPY ./jb-lib jb-lib
WORKDIR /app/jb-lib
RUN poetry build
WORKDIR /app
RUN cp ./jb-lib/dist/*.whl .
RUN rm -rf ./jb-lib

COPY ./logger/pyproject.toml ./logger/poetry.lock ./
# poetry needs a README.md to build the project
RUN touch README.md 

RUN poetry remove lib --group dev
RUN poetry add --lock ./lib-*.whl
RUN poetry install --without dev --sync && rm -rf $POETRY_CACHE_DIR

FROM python:3.11-slim-buster as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./logger/src ./logger

CMD ["python", "-m", "logger"]
