#!/bin/bash

scrapy crawl brandenburg --loglevel=WARNING -s "CLOSESPIDER_ITEMCOUNT=5"
mkdir -p /tmp/data-old
mv data/* /tmp/data-old/

git stash
git checkout master
git stash pop
scrapy crawl brandenburg --loglevel=WARNING -s "CLOSESPIDER_ITEMCOUNT=5"

git diff --no-index /tmp/data-old/brandenburg.json data/brandenburg.json

