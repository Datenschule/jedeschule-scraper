# Changelog

## 2026-04-25
- [BW]: Schools that do not have a Dienststellennummer change their ID
  from an unstable UUID to a more stable hash of name, address, zip and city.
  (that is schools that were `BW-UUID-<something>` become `BW-FB-<something>`)
  ⚠️ This breaks existing ids.
  Schools that are in the dataset right now with UUID ids will be dropped
  from the data that is published through the API and CSV-export.

## 2025-05-12
- [SL]: Switch to data from Geoportal instead of web scraping. We do not get 
  contact details such as email and phone anymore but we (might) get more
  stable ids and also get geolocation data now. ⚠️ This breaks existing ids.

## 2025-04-30
- [BY]: Latitude and Longitude were swapped in the database. This has been fixed.
- [NW]: Latitude and Longitude were swapped in the database. This has been fixed.

## 2025-04-22
- [HH]: The data now includes the location information from the WFS, filling the `location` field in the database
  for the city of Hamburg for the first time
