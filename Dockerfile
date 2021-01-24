FROM scrapinghub/scrapinghub-stack-scrapy:2.4

COPY . .

RUN pip install -r requirements.txt

# Install pg_isready to await db start
RUN apt-get update && \
    apt-get install postgresql-client-11 --yes --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

