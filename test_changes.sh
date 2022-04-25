#!/usr/bin/env bash

set -euxo pipefail

CHANGED_SCRAPERS=$(git whatchanged --name-only --pretty="" origin/master..HEAD  |
                  grep spiders |
                  grep -v helper |
                  sed 's/jedeschule\/spiders\///' |
                  sed 's/\.py//' |
                  sed 's/_/\-/' |
                  uniq || echo "")

if [ -z "$CHANGED_SCRAPERS" ]
then
      echo "No scrapers changed. Exiting"
      exit 0
fi

for SPIDER in $CHANGED_SCRAPERS
do
  echo "=== TESTING CHANGES FOR $SPIDER ==="
  env ENVIRONMENT=TEST scrapy crawl "$SPIDER" \
      -s "CLOSESPIDER_ITEMCOUNT=5" \
       --overwrite-output=/tmp/jedeschule-changes.json \
       --loglevel=WARNING
  python test_changes.py
  rm /tmp/jedeschule-changes.json
done
