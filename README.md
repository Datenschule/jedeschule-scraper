# jedeschule-scraper

Scrapers for German school data. As Germany is a federal country and education is a state level matter every 
state publishes their data differently. The goal of this project is to scraper all data and to make it available
under a common data format.

## Installation
Note that at least Python 3.7 is required.

```bash
pip install -r requirements.txt
```

Make your you have a postgres database running if you want
to use the database pipeline and export an environment
variable pointing to it like so:
```sh
export DATABASE_URL=postgres://postgres@0.0.0.0:5432/jedeschule
```
Then, run the migrations to bring you database up to date
```sh
alembic upgrade head
```


## Testing
To run some very basic integration tests run:
```
./test.sh
```

## Running:

```bash
./run.py
```

The script will generate a new directory "data". The result of each scraper is available as json file

Sources:

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
