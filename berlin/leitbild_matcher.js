var jsonfile = require('jsonfile');
var _ = require('lodash');

var main_file = __dirname + '/schools_raw.json';
var concept_file = __dirname + '/schools.json';
var output_file = __dirname + '/schools_merged.json';

jsonfile.readFile(main_file, function(err, main) {
    jsonfile.readFile(concept_file, function(err, concept) {
        var merged = main.map(function(m) {
            var counterpart = _.find(concept, ['code', m.code])
            if (counterpart) {
                var concepthtml = _.find(counterpart.statistics, ['name', 'Leitbild'])
                if (concepthtml)
                    m['leitbild_html'] = concepthtml.rows
            } else {
                console.log('Corresponding school for ' + m.code + 'not found');
            }
            return m;
        })
        jsonfile.writeFile(output_file, merged, function(err) {
            console.log('merge finished')
        })
    })
})
