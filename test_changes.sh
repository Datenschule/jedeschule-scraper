#!/usr/bin/env bash

set -e

if [ $CI ]
then
  HEAD_REF=${GITHUB_REF}
else
  HEAD_REF="HEAD"
fi

echo "Using head reference: ${HEAD_REF}"

CHANGED_SCRAPERS=$(git whatchanged --name-only --pretty="" origin/master..${HEAD_REF}  |
                  grep spiders |
                  grep -v helper |
                  sed 's/jedeschule\/spiders\///' |
                  sed 's/\.py//' |
                  sed 's/_/\-/' |
                  uniq)

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
