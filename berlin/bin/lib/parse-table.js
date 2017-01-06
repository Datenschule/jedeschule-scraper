'use strict';

function parseValue(value) {
  let asString = value.replace(/\./g, '').replace(',', '.');
  let asNumber = +asString;
  if (/^[-0-9\.]+$/.test(asString)) return asNumber;
  return asString;
}

module.exports = function ($, $table) {
  let name = $table.find('caption').text().trim();

  let $rows = $table.find('tr');

  if ($rows.text().trim() === 'Für Ihre aktuelle Anfrage sind keine Daten verfügbar.') {
    return { name, rows: null, notAvailable: true };
  }

  let headers = [];
  let rows = [];

  $rows.each((i, tr) => {
    let row;
    $(tr).find('th, td').each((i, cell) => {
      if ($(cell).is('th')) {
        let header = $(cell).text().trim();
        if (header) headers[i] = header;
      } else {
        if (headers.length) {
          if (!row) {
            row = {};
            rows.push(row);
          }
          let header = headers[i] || i;
          row[header] = parseValue($(cell).text().trim());
        } else {
          if (!row) {
            row = [];
            rows.push(row);
          }
          row[i] = parseValue($(cell).text().trim());
        }
      }
    });
  });

  if (headers.length) {
    return { name, rows };
  } else {
    // Check if the table might be laid out vertically, with the headers
    // in the leftmost column and not marked up as such
    let tableIsHorizontal = true;
    rows.forEach(row => {
      if (!tableIsHorizontal) return;
      if (row.length !== 2) tableIsHorizontal = false;
    });
    if (tableIsHorizontal) {
      let oldRows = rows;
      rows = {};
      oldRows.forEach(row => rows[row[0]] = row[1]);
    }
    return { name, rows };
  }
}
