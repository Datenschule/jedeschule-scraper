FROM scrapinghub/scrapinghub-stack-scrapy:2.11

COPY . .

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv sync --locked --all-extras

# Install pg_isready to await db start
RUN apt-get update && \
    apt-get install postgresql-client --yes --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

