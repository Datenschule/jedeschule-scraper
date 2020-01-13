FROM scrapinghub/scrapinghub-stack-scrapy:1.8-py3

COPY . .

RUN pip install -r requirements.txt

# Install pg_isready to await db start
RUN apt-get update
RUN apt-get install postgresql-client-11 cron --yes

# Add crontab file in the cron directory
ADD crontab /etc/cron.d/scrape-schools

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/scrape-schools

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD bash ./run.sh && bash ./scrape_all.sh && cron && tail -f /var/log/cron.log

