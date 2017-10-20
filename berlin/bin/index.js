'use strict';

const ProgressBar = require('progress');
const cheerio = require('cheerio');
const async = require('async');
const URL = require('url');
const pr = require('path').resolve;
const fs = require('fs-extra');
const scrapyard = require('scrapyard');

var scraper = new scrapyard({
    debug: true,
    retries: 5,
    connections: 10,
    //cache: './storage',
    //bestbefore: "5min"
});

const fetch = require('./lib/fetch')({ cacheDir: pr(__dirname, '../.fetch-cache') });
const fetchSchool = require('./lib/fetch-school');

const OUTPUT_DIR = pr(__dirname, '../output');

function scrape(url, method = 'GET', formdata) {
    return new Promise(function(fulfill, reject) {
        scraper({
            url: url,
            type: 'html',
            method: method,
            form: formdata,
            jar:true
        }, function(err, $) {
            if (err) {
                reject(err);
            }
            else {
                fulfill($);
            }
        });
    });
}

function parseSchoollist($) {
    //let $ = cheerio.load(body);
    let url = 'http://www.berlin.de/sen/bildung/schulverzeichnis_und_portraets/anwendung/SchulListe.aspx';
    let $rows = $('#DataListSchulen tr:not(:first-of-type)');
    let schools = $rows.map((i, tr) => ({
        id: $(tr).find('a').attr('href').split('?IDSchulzweig=')[1],
        code: $(tr).find('a').text(),
        entryURL: URL.resolve(url, $(tr).find('a').attr('href')),
        name: $(tr).find('td span').eq(0).text(),
        type: $(tr).find('td span').eq(1).text(),
        bezirk: $(tr).find('td span').eq(2).text(),
        ortsteil: $(tr).find('td span').eq(3).text(),
    })).get();
    return schools;
}


function getSchoolList(schools, postdata, index) {

    return new Promise(function (fulfill, reject) {
        scrape('https://www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/SchulListe.aspx', 'POST', postdata)
            .then(($) => {
                var new_schools = parseSchoollist($);
                //var $ = cheerio.load(data);
                var postdata = {
                    "__EVENTTARGET" : "GridViewSchulen",
                    "__EVENTARGUMENT" : 'Page$' + (index + 1),
                    "__VIEWSTATE" : $('#__VIEWSTATE').attr('value'),
                    "__VIEWSTATEGENERATOR" : $('#__VIEWSTATEGENERATOR').attr('value'),
                    "__VIEWSTATEENCRYPTED" : $('#__VIEWSTATEENCRYPTED').attr('value'),
                    "__EVENTVALIDATION" : $('#__EVENTVALIDATION').attr('value')
                };
                schools = schools.concat(new_schools);
                if (new_schools.length == 41) {
                    console.log('requesting page ' + (index + 1));
                    return getSchoolList(schools, postdata, index + 1)
                }
                else {
                    fulfill(schools);
                }
            })
            .then((data) => {
                fulfill(data)
            })
            .catch(console.log);
    })
}


getSchoolList([], {}, 1)
//  .then(schools => schools.filter(school => school.name === 'Albert-Einstein-Gymnasium'))
  .then(schools => {
    let bar = new ProgressBar(':bar :percent (:token1)', { total: schools.length });

    async.eachSeries(schools, (school, schoolDone) => {
      let outputPath = pr(OUTPUT_DIR, school.id + '.json');
      try {
        JSON.parse(fs.readFileSync(outputPath));
        bar.tick({ token: school.code });
        return schoolDone();
      } catch (e) {
        //if (e.code !== 'ENOENT') throw e;
      }
      fetchSchool(school)
        .then(school => {
          bar.tick({ token: school.code });
          fs.outputFile(
            outputPath,
            JSON.stringify(school),
            schoolDone );
        })
        .catch(schoolDone);
    }, function allDone(err) {
      if (err) console.error(err.stack);
      let data = fs.readdirSync(OUTPUT_DIR)
        .filter(file => /\.json$/.test(file))
        .map(file => JSON.parse(fs.readFileSync(pr(OUTPUT_DIR, file))));
      fs.outputFileSync('schools.json', JSON.stringify(data));
    });
  })
  .catch(e => console.error(e.stack));
