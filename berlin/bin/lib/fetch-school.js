'use strict';

const cheerio = require('cheerio');
const async = require('async');
const URL = require('url');
const pr = require('path').resolve;
const _ = require('lodash');

const fetch = require('./fetch')({ cacheDir: pr(__dirname, '../../.fetch-cache') });
const parseTable = require('./parse-table');

let queueErrorHandler = function (error) { if (error) console.error(error.stack); }

module.exports = school => new Promise((resolve, reject) => {
  school = _.cloneDeep(school);
  let completionHandlers = {
    navigation: function (body, task) {
      let $ = cheerio.load(body);
      let school = task.school;
      let navigationLinks = $('#portrait_hauptnavi a');
      navigationLinks.each((i, a) => {
        let href = $(a).attr('href');
        if (href === 'Schulportrait.aspx') return;

        let url;
        try {
          url = URL.resolve(task.url, href);
        } catch (e) {
          console.warn('Ignoring %s due to error (%s)', href, e.stack);
          return;
        }
        if (school._visitedURLs[url]) return;
        school._visitedURLs[url] = true;

        let complete;
        if (href.indexOf('schuelerschaft') !== -1) complete = completionHandlers.statistics;
        else if (href.indexOf('schulpersonal') !== -1) complete = completionHandlers.statistics;
        else if (href.indexOf('ressourcen') !== -1) complete = completionHandlers.statistics;
        else if (href.indexOf('schulprogramm') !== -1) complete = completionHandlers.statistics;
        else if (href.indexOf('modellschulversuche') !== -1) complete = completionHandlers.statistics;
        else if (href.indexOf('management') !== -1) complete = completionHandlers.statistics;
        else complete = completionHandlers.generic;

        queue.push({ url, school, complete }, queueErrorHandler);
      });
    },

    schoolIndex: function (body, task) {
      let $ = cheerio.load(body);
      let school = task.school;
      school.address = {};
      school.address.street = $('#ContentPlaceHolderMenuListe_lblStrasse').text();
      let plzOrt = $('#ContentPlaceHolderMenuListe_lblOrt').text().match(/^(\d{5})? ?(.*)$/);
      if (plzOrt) {
        school.address.postcode = plzOrt[1];
        school.address.city = plzOrt[2];
      }
      school.legal_status = $('#ContentPlaceHolderMenuListe_lblSchulart').text().match(/\((.*?)\)/)[1].trim();
      school.phone = $('#ContentPlaceHolderMenuListe_lblTelefon').text();
      school.fax = $('#ContentPlaceHolderMenuListe_lblFax').text();
      school.email = $('#ContentPlaceHolderMenuListe_HLinkEMail').text();
      school.website = $('#ContentPlaceHolderMenuListe_HLinkWeb').attr('href');
      school.headmaster = $('#ContentPlaceHolderMenuListe_lblLeitung').text();
      school.languages = $('#ContentPlaceHolderMenuListe_lblSprachen').text();
      school.offers = $('#ContentPlaceHolderMenuListe_lblAngebote').text();
      school.facilities = $('#ContentPlaceHolderMenuListe_lblAusstattung').text();
      school.clubs = $('#ContentPlaceHolderMenuListe_lblAGs').text();
      school.furtherOffer = $('#ContentPlaceHolderMenuListe_lblZusatzText').text();
      school.cooperations = $('#ContentPlaceHolderMenuListe_lblKoop').text();
      school.partner = $('#ContentPlaceHolderMenuListe_lblPartner').text();
      school.lunch = $('#ContentPlaceHolderMenuListe_lblMittag').text();
      school.majorFields = $('#ContentPlaceHolderMenuListe_lblLeistungskurse').text();

      school._visitedURLs = {};
      school._visitedURLs[task.url] = true;

      school.statistics = {};

      completionHandlers.navigation(body, task);
    },

    statistics: function (body, task) {
      let $ = cheerio.load(body);
      let $table = $('#RechteSeite table');

      let statistic = parseTable($, $table);
      task.school.statistics[statistic.name] = statistic.rows;

      completionHandlers.navigation(body, task);
    },

    generic: function (body, task) {
      completionHandlers.navigation(body, task);
    },
  };


  let url = school.entryURL;

  let queue = async.queue(function worker(task, callback) {
    fetch(task.url, task.school)
      .then(body => { task.complete(body, task); callback(); })
      .catch(callback);
  }, 5);

  queue.push({
    url,
    school,
    complete: completionHandlers.schoolIndex,
  }, queueErrorHandler);

  queue.drain = function () {
    delete school._visitedURLs;
    school.statistics = _(school.statistics)
      .map((rows, name) => ({ name, rows }))
      .sortBy('name')
      .values();

    resolve(school);
  }
});
