'use strict';

const pr = require('path').resolve;
const fs = require('fs');
const _ = require('lodash');

let schools = JSON.parse(fs.readFileSync(pr(__dirname, '../schools.json')));

process.stdout.write([ 'Schule', 'Ortsteil', 'Statistik', 'Jahr', 'Spalte', 'Wert' ].join('\t') + '\n');

_(schools).each(school => {
  _(school.statistics)
    .each(statistic => {
      let nameAndYear = statistic.name.match(/^(.*) (\d{4}\/\d{2}.*?)$/);
      if (nameAndYear) {
        statistic.name = nameAndYear[1];
        statistic.year = nameAndYear[2];
      }

      if (!statistic.year) return;

      _([ statistic.rows ]).flatten().each(row => {
        _(row).each((value, key) => {
          if (!value) return;
          value = value.toString().replace(/[\t\n\r]/g, '');
          if (value.length > 10) return;
          let output = [ school.name, school.ortsteil, statistic.name, statistic.year, key, value ].join('\t');
          process.stdout.write(output + '\n');
        })
      });
    });
});
