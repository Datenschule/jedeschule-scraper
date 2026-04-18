# BW fresh-run stable ID analysis (clean DB)

Date: 2026-04-18  
Branch: `bw-stable-id-only`  
Spider: `baden-wuerttemberg`  
Environment: `jedeschule-docker-test` (DB truncated before crawl by pipeline script)

## Repro commands

```bash
cd /Users/tordans/Development/OSM/schul-vergleich-workspace/jedeschule-docker-test
docker compose down
SCRAPER_SPIDER=baden-wuerttemberg docker compose run --rm scraper
```

The crawl script runs:

1. `alembic upgrade head`
2. `TRUNCATE TABLE schools CASCADE`
3. `scrapy crawl baden-wuerttemberg`

## Results summary

### Crawl stats

- `item_scraped_count`: **5727** (from Scrapy stats at end of run)
- one WFS request, finished successfully

### Stored BW rows (clean DB)

```sql
SELECT count(*) AS bw_total FROM schools WHERE id LIKE 'BW-%';
```

- `bw_total`: **5512**

```sql
SELECT
  CASE
    WHEN id LIKE 'BW-UUID-%' THEN 'BW-UUID'
    WHEN id LIKE 'BW-FB-%' THEN 'BW-FB'
    WHEN id ~ '^BW-[0-9]{8}$' THEN 'BW-DISCH'
    ELSE 'BW-OTHER'
  END AS id_kind,
  count(*)
FROM schools
WHERE id LIKE 'BW-%'
GROUP BY 1
ORDER BY 2 DESC;
```

- `BW-DISCH`: **4421**
- `BW-FB`: **1089**
- `BW-UUID`: **2**
- `BW-OTHER`: **0**

## UUID fallback residues

Residual UUID rows:

1. `BW-UUID-2e4484b3-aae9-471f-a0a7-4d2d834717ab`  
   `Zentrum für Schulqualität und Lehrerbildung (ZSL) Außenstelle Ludwigsburg`
2. `BW-UUID-6dfe1ac8-8b25-442a-ab15-e938288d0def`  
   `InzTanz Internationales Zentrum für Tanz`

Signal profile:

```sql
SELECT
  count(*) AS uuid_rows,
  count(*) FILTER (WHERE location IS NULL) AS location_null,
  count(*) FILTER (WHERE coalesce(address,'')='') AS address_blank,
  count(*) FILTER (WHERE coalesce(zip,'')='') AS zip_blank,
  count(*) FILTER (WHERE coalesce(city,'')='') AS city_blank,
  count(*) FILTER (WHERE coalesce(name,'')='') AS name_blank,
  count(*) FILTER (WHERE coalesce(school_type,'')='') AS school_type_blank
FROM schools
WHERE id LIKE 'BW-UUID-%';
```

- `uuid_rows`: 2
- both have `location IS NULL`
- both still have non-empty `name`, `school_type`, `address`, `zip`, `city`

### Why UUID is still used

Current fallback path in `baden_wuerttemberg`:

- DISCH from email -> `BW-{disch}`
- else if coordinates available -> `BW-FB-{hash}`
- else -> `BW-UUID-{feature_uuid}`

So these 2 rows use UUID only because coordinates were missing in source.

## ID conflicts / overwrite behavior in a clean run

From the crawl log (`<School id=...>` lines):

- scraped IDs: **5727**
- unique generated IDs: **5512**
- overwrite events due duplicate generated IDs: **215**
- duplicated generated IDs: **185**

Duplicate events by ID family:

- `BW-DISCH`: **201**
- `BW-FB`: **14**
- `BW-UUID`: **0**

Observed duplicates had the same ID and same school name in log parsing (no mixed-name duplicate IDs found).  
This points to repeated source records for the same school ID/signature, not hash collisions with different school cores.

## Suggested next stable fallback for no-coordinate residues

For rows without DISCH and without coordinates, use deterministic secondary fallback before UUID:

1. `BW-FBA-{hash}` from normalized:
   - `name`
   - `school_type`
   - `address`
   - `zip`
   - `city`
2. if these are insufficient / empty, then `BW-UUID-{feature_uuid}`

Why this is feasible here:

- in this fresh run, all residual UUID rows had all five address/name/type signals present.

Risk notes:

- address renames or formatting changes can re-key rows (less stable than coordinate-based FB).
- same institution at same postal address with same type and same name normalization would intentionally collapse.
- keep UUID as final fallback to avoid dropping rows when even address signals are absent.

## Conclusion

Stable fallback significantly reduced unstable UUID ids:

- from 1105 UUID rows in a stale/image-mismatch run to **2 UUID rows** in a clean rebuilt run.
- remaining UUIDs are explainable by missing coordinates only.

The branch goal (stable-ID-only) is met; timestamp/`last_seen` changes are excluded.
