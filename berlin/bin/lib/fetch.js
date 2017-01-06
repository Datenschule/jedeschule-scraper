'use strict';

const request = require('request');
const pr = require('path').resolve;
const fs = require('fs-extra');

let cookieJars = {};
let schoolEntryURL = 'http://www.berlin.de/sen/bildung/schulverzeichnis_und_portraets/anwendung/Schulportrait.aspx?IDSchulzweig=';

module.exports = function (config) {
  config = config || {};
  let debug = config.debug;
  let cacheDir = config.cacheDir || '.fetch-cache/';

  return function fetch(url, school) {
    school = school || {};

    return new Promise((resolve, reject) => {
      let cachePath = pr(cacheDir, school.id || '', url.replace(/^.*\/anwendung\//, ''));
      fs.readFile(cachePath, (err, data) => {
        if (data) {
          if (debug) console.log('Found in cache');
          return resolve(data);
        }

        let cookieJar = false;

        function fetchPageFromWeb(jar) {
          if (debug) console.log(school.id, 'Fetching page from web');
          jar = jar || cookieJar;
          request(url, { jar }, (err, response, body) => {
            if (err) return reject(err);
            fs.outputFile(cachePath, body);
            resolve(body);
          });
        }

        // Check if we're fetching a school sub-page
        if (/Schulportrait|SchulListe/.test(url)) {
          // No, it's probably just a normal page
          if (debug) console.log(school.id, 'Session not necessary');
          fetchPageFromWeb();
        } else {
          // Yes, it's a school-subpage
          // This means that we need to have established a session already
          if (debug) console.log(school.id, 'Session necessary');
          if (!school.id) return reject(new Error('Tried to fetch a school sub-page, but no school.id was provided'));
          cookieJar = cookieJars[school.id];
          if (cookieJar) {
            if (debug) console.log(school.id, 'Cookie jar already established');
            if (cookieJar.pending) {
              if (debug) console.log(`But it's pending`);
              cookieJar.onDone.push(fetchPageFromWeb);
            } else {
              fetchPageFromWeb();
            }
          } else {
            if (debug) console.log(school.id, 'Cookie jar not yet established');
            // Open a new cookie jar …
            cookieJar = request.jar();
            // … but don't store it in the lookup table yet – or else we'd
            // run into a race condition if we get requests for several
            // sub-pages of the same school before we've established a sesssion
            // for the first time.
            // Instead, create a temporary 'pending' object with an array
            // that lets us store the 'fetchPageFromWeb' callback for later
            cookieJars[school.id] = { pending: true, onDone: [] };
            // Visit the appropriate entry page first to get a session cookie
            request(schoolEntryURL + school.id, { jar: cookieJar }, err => {
              if (debug) console.log(school.id, 'Cookie initialized');
              if (err) return reject(err);
              else {
                fetchPageFromWeb();
                cookieJars[school.id].onDone.forEach(callback => callback(cookieJar));
                cookieJars[school.id] = cookieJar;
              }
            });
          }
        }
      });
    });
  }
}
