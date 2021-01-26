#!/usr/bin/env bash


for spider in $(scrapy list)
do
  # In case of errors with this spider, we want to exit early
  # to not overlad the target website with requests that we 
  # cannot even use in the end.
  # This is why we set the maximum amount of items that are
  # allowed to crash to 3 here.
  scrapy crawl $spider -s "CLOSESPIDER_ERRORCOUNT=3" --loglevel=INFO
done
