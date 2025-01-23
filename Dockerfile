FROM scrapinghub/scrapinghub-stack-scrapy:2.11

COPY . .

RUN pip install -r requirements.txt

# Install pg_isready to await db start
RUN apt-get update && \
    apt-get install postgresql-client --yes --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

