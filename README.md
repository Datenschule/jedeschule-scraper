# jedeschule-scraper

Scrapers for German school data. As Germany is a federal country and education is a state level matter every 
state publishes their data differently. The goal of this project is to scraper all data and to make it available
under a common data format.

## Installation
Note that at least Python 3.7 is required.

```bash
pip install -r requirements.txt
```

Make your you have a postgres database with postgis support 
running if you want to use the database pipeline and expor
t an environment variable pointing to it like so:
```sh
export DATABASE_URL=postgres://postgres@0.0.0.0:5432/jedeschule
```
Then, run the migrations to bring you database up to date
```sh
alembic upgrade head
```


## Testing
To run some very basic integration tests, you will need another postgres
database for test data. After creating it, run the following steps 
(assuming you called your database `jedeschule_scraper_test`):
```
export DATABASE_URL=postgres://postgres@0.0.0.0:5432/jedeschule_scraper_test
alembic upgrade head
python test_models.py
```

If you made changes to scrapers, you can also run a script to check the 
changes between your new scraper results and the data that is currently
hosted on the server at jedeschule.codefor.de.

To do so, run the `./test_changes.sh` script on your feature branch. This
will find the scrapers that have been changed on your branch and will then run
them to get some sample data. For each fetched result, it will call the upstream API
and compare the results for this ID. Note that the script always returns
with a 0 exit code, hence you need to evaluate the changes manually.

## Running:
### Updating data for all states
To update data for all states, run
```bash
bash ./scrape_all.sh
```

### Updating data for a single state
To get updates for a single state, run
```bash
scrapy crawl <state_name>
# use `scrapy list` to get a list of all available states
```

## Deployment
You can deploy the scrapers directly on a server or using Docker. The resulting Docker
image needs to be run with the `DATABASE_URL` environment variable pointing to a Postgres
instance. You can for example use docker-compose to achieve this. See the
[docker-compose file at jedeschule-api](https://github.com/codeforberlin/jedeschule-api/blob/master/docker-compose.yml)
for inspiration.

## Updating data on jedeschule.codefor.de
There is a version of these scrapers (and an instance of [jedeschule-api](
https://github.com/codeforberlin/jedeschule-api)) that is deployed at
jedeschule.codefor.de.
The deployment uses docker-compose. To update the data there, login as the
`jedeschule` user and run the commands mentioned int the previous section
prefixed with `sudo docker-compose run scrapers`. This means that if you
want to for example get the newest data for Berlin you would run `sudo docker-compose run scrapers scrapy crawl berlin`


## Sources
* Schulverzeichnis Bayern: [https://www.bllv.de/index.php?id=2707](https://www.bllv.de/index.php?id=2707)
* Schulportraits Brandenburg: [https://www.bildung-brandenburg.de/schulportraets/index.php?id=3&schuljahr=2016&kreis=&plz=&schulform=&jahrgangsstufe=0&traeger=0&submit=Suchen](https://www.bildung-brandenburg.de/schulportraets/index.php?id=3&schuljahr=2016&kreis=&plz=&schulform=&jahrgangsstufe=0&traeger=0&submit=Suchen)
* Schulwegweiser Bremen: [http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d](http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d)
* Schulverzeichnis Niedersachsen: [http://schulnetz.nibis.de/db/schulen/suche_2.php](http://schulnetz.nibis.de/db/schulen/suche_2.php)
* Schulverzeichnis "Schule suchen" NRW:[http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d](http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d)
* Schuladressen Saarland: [http://www.saarland.de/4526.htm](http://www.saarland.de/4526.htm)
* Schuldatenbank Sachsen: [https://schuldatenbank.sachsen.de/index.php?id=2](https://schuldatenbank.sachsen.de/index.php?id=2)
* Schulsuche Sachsen Anhalt: [https://www.bildung-lsa.de/ajax.php?m=getSSResult&q=&lk=-1&sf=-1&so=-1&timestamp=1480082277128/](https://www.bildung-lsa.de/ajax.php?m=getSSResult&q=&lk=-1&sf=-1&so=-1&timestamp=1480082277128/)
* Schulportrait Schleswig Holstein: [http://schulportraets.schleswig-holstein.de/portal/schule_suchen/](http://schulportraets.schleswig-holstein.de/portal/schule_suchen/)
* Schulportal Thüringen: [https://www.schulportal-thueringen.de/tip/schulportraet_suche/search.action?tspi=&tspm=&vsid=none&mode=&extended=0&anwf=schulportraet&freitextsuche=&name=&schulnummer=&strasse=&plz=&ort=&schulartDecode=&schulamtDecode=&schultraegerDecode=&sortierungDecode=Schulname&rowsPerPage=999&schulartCode=&schulamtCode=&schultraegerCode=&sortierungCode=10&uniquePortletId=portlet_schulportraet_suche_WAR_tip_LAYOUT_10301](https://www.schulportal-thueringen.de/tip/schulportraet_suche/search.action?tspi=&tspm=&vsid=none&mode=&extended=0&anwf=schulportraet&freitextsuche=&name=&schulnummer=&strasse=&plz=&ort=&schulartDecode=&schulamtDecode=&schultraegerDecode=&sortierungDecode=Schulname&rowsPerPage=999&schulartCode=&schulamtCode=&schultraegerCode=&sortierungCode=10&uniquePortletId=portlet_schulportraet_suche_WAR_tip_LAYOUT_10301)
* Rheinland Pfalz: [https://www.statistik.rlp.de/service/adress-suche/](https://www.statistik.rlp.de/service/adress-suche/)
