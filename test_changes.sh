#!/usr/bin/env bash

set -euxo pipefail

git fetch origin main

if [ "${CI:-}" = "true" ]; then
  HEAD_REF="${GITHUB_SHA}"
else
  HEAD_REF="HEAD"
fi

echo "Using head reference: ${HEAD_REF}"

CHANGED_SCRAPERS=$(git diff --name-only origin/main..."${HEAD_REF}"  |
                  grep spiders  |
                  grep -v helper  |
                  sed 's|jedeschule/spiders/||' |
                  sed 's|\.py||' |
                  sed 's|_|-|' |
                  sort -u) || true

if [ -z "$CHANGED_SCRAPERS" ]; then
    echo "No scrapers were changed"
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
