# jedeschule-scraper

Scrapers for German school data. As Germany is a federal country and education is a state level matter every 
state publishes their data differently. The goal of this project is to scraper all data and to make it available
under a common data format.

## Using the data
A version of these scrapers is deployed at [https://jedeschule.codefor.de/](jedeschule.codefor.de).
You can use it one of three ways:
1. Using the API. Documentation is available at https://jedeschule.codefor.de/docs
2. Using the CSV dump provided at https://jedeschule.codefor.de/csv-data/
3. Exploring the data using a small interactive dashboard at: https://knutator2.github.io/jedeschule-explore/#/dashboard

## IDs
We try to use stable IDs for the data we publish so that it is comparable
across time. We do however have to rely on the data publishers providing
IDs that we can re-use. To avoid collisions, we prefix the IDs with the state's
ISO-3166-2 code (without the `DE-` prefix).

In details, the IDs are sourced as follows:


|State| ID-Source                                                                                                    | exmaple-id                                                                 |stable|
|-----|--------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|------|
|BW| Field `DISCH` (Dienststellenschüssel) in the JSON repsonse                                                   | `BW-04154817`                                                              |✅ likely|
|BY| id from the WFS service                                                                                      | `BY-SCHUL_SCHULSTANDORTEGRUNDSCHULEN_2acb7d31-915d-40a9-adcf-27b38251fa48` |❓ unlikely (although we reached out to ask for canonical IDs to be published)|
|BE| Field `bsn` (Berliner Schulnummer) from the WFS Service                                                      | `BE-02K10`                                                                 |✅ likely|
|BB| Field `schul_nr` (Schulnummer) from thw WFS Service                                                          | `BB-111430`                                                                |✅ likely|
|HB| `id` URL query param on the school's detail page (identical to the SNR (Schulnummer) from the overview page) | `HB-937`                                                                   |✅ likely|
|HH| Field `schul_id` From the WFS Service                                                                        | `HH-7910-0`                                                                |✅ likely|
|HE| `school_no` URL query param of the schools's details page (identical to the Dienststellennummer)             | `HE-4024`                                                                  |✅ likely|
|MV| Column `DIENSTSTELLEN-NUMMER` from the XLSX file                                                             | `MV-75130302`                                                              |✅ likely|
|NI| Field `schulnr` from the JSON in the details payload                                                         | `NI-67763`                                                                 |✅ likely|
|NW| Column `Schulnummer` from the CSV                                                                            | `NW-162437`                                                                |✅ likely|
|RP| `Schulnummer` from the school's details page                                                                 | `RP-50720`                                                                 |✅ likely|
|SL| `OBJECTID` from the WFS service                                                                              | `SL-255`                                                                   |❓ unlikely |
|SN| Field `id` from the API                                                                                      | `SN-4062`                                                                  |✅ likely|
|ST| `ID` query param from the details page URL                                                                   | `ST-1001186`                                                               |❓ probably?|
|TH| `Schulnumer` from school list                                                                                | `TH-10601`                                                                 |✅ likely|

## Geolocations
When available, we try to use the geolocations provided by the data publishers.

| State | Geolcation available | Source                                       |
|-------|----------------------|----------------------------------------------|
| BW    | ❌ No                 | -                                            |
| BY    | ✅ Yes                | WFS                                          |
| BE    | ✅ Yes                | WFS                                          |
| BB    | ✅ Yes                | WFS                                          |
| HB    | ❌ No                 | -                                            |
| HH    | ✅ Yes                | WFS                                          |
| HE    | ❌ No                 | -                                            |
| MV    | ❌ No                 | -                                            |
| NI    | ❌ No                 | -                                            |
| NW    | ✅ Yes                | Converted from EPSG:25832 in source CSV data |
| RP    | ❌ No                 | -                                            |
| SL    | ✅ Yes                | WFS                                          |
| SN    | ✅ Yes                | API                                          |
| ST    | ❌ No                 | -                                            |
| TH    | ❌ No                 | -                                            |

## Installation
Dependency management is done using [uv](https://docs.astral.sh/uv/). Make sure
to have it installed and then run the following command to install the dependencies:

```bash
uv sync --locked --all-extras
```

Make your you have a postgres database with postgis support 
running if you want to use the database pipeline and expor
t an environment variable pointing to it like so:
```sh
export DATABASE_URL=postgres://postgres@0.0.0.0:5432/jedeschule
```
Then, run the migrations to bring you database up to date
```sh
uv run alembic upgrade head
```


## Testing
To run some very basic integration tests, you will need another postgres
database for test data. After creating it, run the following steps 
(assuming you called your database `jedeschule_scraper_test`):
```
export DATABASE_URL=postgres://postgres@0.0.0.0:5432/jedeschule_scraper_test
uv run alembic upgrade head
uv run python test_models.py
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
uv run scrapy crawl <state_name>
# use `scrapy list` to get a list of all available states
```

## Deployment
You can deploy the scrapers directly on a server or using Docker. The resulting Docker
image needs to be run with the `DATABASE_URL` environment variable pointing to a Postgres
instance. You can for example use docker-compose to achieve this. See the
[docker-compose file at jedeschule-api](https://github.com/codeforberlin/jedeschule-api/blob/main/docker-compose.yml)
for inspiration.

## Updating data on jedeschule.codefor.de
There is a version of these scrapers (and an instance of [jedeschule-api](
https://github.com/codeforberlin/jedeschule-api)) that is deployed at
jedeschule.codefor.de.
The deployment uses docker-compose. To update the data there, login as the
`jedeschule` user and run the commands mentioned int the previous section
prefixed with `sudo docker-compose run scrapers`. This means that if you
want to for example get the newest data for Berlin you would run `sudo docker-compose run scrapers scrapy crawl berlin`

