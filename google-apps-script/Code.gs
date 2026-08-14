const DATA_URL = 'https://raw.githubusercontent.com/Stats-w-Sass/CAER-Monitor/main/data/caer_messages.json';
const TARGET_SHEET_ID = '1l9dbT-NsvKrPSby63Kko6GmO3fgPfKXQGTl4PR1qfNo';

const SHEET_LAYOUT = {
  'Current Messages': [
    'Status',
    'Facility',
    'Posted Date',
    'Posted Time',
    'Tags',
    'Message',
    'First Seen',
    'Last Seen',
    'Source',
    'Previously Seen',
    'Message ID'
  ],
  'New Messages': [
    'Status',
    'Facility',
    'Posted Date',
    'Posted Time',
    'Tags',
    'Message',
    'First Seen',
    'Last Seen',
    'Source',
    'Previously Seen',
    'Message ID'
  ],
  'Still Posted': [
    'Facility',
    'Posted Date',
    'Posted Time',
    'Tags',
    'Message',
    'First Seen',
    'Last Seen',
    'Number of Observations',
    'Source'
  ],
  'Cleared Messages': [
    'Facility',
    'Posted Date',
    'Posted Time',
    'Tags',
    'Message',
    'First Seen',
    'Last Seen',
    'Cleared Date/Time',
    'Duration Active',
    'Source'
  ],
  'App vs Website': [
    'Message ID',
    'Facility',
    'Posted Date/Time',
    'Website',
    'Mobile App/API',
    'First Seen',
    'Last Seen',
    'Tags',
    'Message'
  ],
  'Data Dictionary': [
    'Field',
    'Description'
  ]
};

function onOpen() {
  createTimeTrigger();
  SpreadsheetApp.getUi()
    .createMenu('CAER')
    .addItem('Refresh Data', 'refreshData')
    .addToUi();
}

function parsePostedDateTime(value) {
  if (!value) {
    return ['', ''];
  }

  const parsed = new Date(value);
  if (isNaN(parsed.getTime())) {
    return [String(value), ''];
  }

  const tz = Session.getScriptTimeZone() || 'UTC';
  return [
    Utilities.formatDate(parsed, tz, 'yyyy-MM-dd'),
    Utilities.formatDate(parsed, tz, 'HH:mm:ss')
  ];
}

function normalizeTags(categoryList) {
  const categories = Array.isArray(categoryList) ? categoryList : [];
  return categories.filter(Boolean).join('; ');
}

function sourceLabel(sourceUrl) {
  const url = String(sourceUrl || '').toLowerCase();
  if (url.includes('mobile') || url.includes('app')) {
    return 'Mobile API';
  }
  if (url.includes('archive')) {
    return 'Archive';
  }
  return 'Website';
}

function getRecordStatus(record) {
  return String(record.status || '').trim();
}

function renderCurrentRows(records) {
  const rows = [];
  const active = records.filter(function (record) {
    return String(record.status || '').trim() !== 'cleared';
  });

  const ordered = active.sort(function (a, b) {
    return new Date(b.posted_datetime || 0) - new Date(a.posted_datetime || 0);
  });

  ordered.forEach(function (record) {
    const [postedDate, postedTime] = parsePostedDateTime(record.posted_datetime);
    rows.push([
      getRecordStatus(record),
      String(record.facility || ''),
      postedDate,
      postedTime,
      normalizeTags(record.category),
      String(record.message_text || ''),
      String(record.first_seen || ''),
      String(record.last_seen || ''),
      sourceLabel(record.source_url),
      record.previously_seen ? 'TRUE' : 'FALSE',
      String(record.message_id || '')
    ]);
  });

  return rows;
}

function renderNewRows(records) {
  const rows = [];
  const newRecords = records.filter(function (record) {
    return String(record.status || '').trim() === 'new';
  });

  newRecords.sort(function (a, b) {
    return new Date(b.posted_datetime || 0) - new Date(a.posted_datetime || 0);
  }).forEach(function (record) {
    const [postedDate, postedTime] = parsePostedDateTime(record.posted_datetime);
    rows.push([
      getRecordStatus(record),
      String(record.facility || ''),
      postedDate,
      postedTime,
      normalizeTags(record.category),
      String(record.message_text || ''),
      String(record.first_seen || ''),
      String(record.last_seen || ''),
      sourceLabel(record.source_url),
      record.previously_seen ? 'TRUE' : 'FALSE',
      String(record.message_id || '')
    ]);
  });

  return rows;
}

function renderStillPostedRows(records) {
  const rows = [];
  const relevant = records.filter(function (record) {
    return String(record.status || '').trim() === 'previous message still posted';
  });

  relevant.sort(function (a, b) {
    return new Date(b.posted_datetime || 0) - new Date(a.posted_datetime || 0);
  }).forEach(function (record) {
    const [postedDate, postedTime] = parsePostedDateTime(record.posted_datetime);
    rows.push([
      String(record.facility || ''),
      postedDate,
      postedTime,
      normalizeTags(record.category),
      String(record.message_text || ''),
      String(record.first_seen || ''),
      String(record.last_seen || ''),
      Array.isArray(record.versions) ? String(record.versions.length) : '1',
      sourceLabel(record.source_url)
    ]);
  });

  return rows;
}

function renderClearedRows(records) {
  const rows = [];
  const relevant = records.filter(function (record) {
    return String(record.status || '').trim() === 'cleared';
  });

  relevant.sort(function (a, b) {
    return new Date(b.posted_datetime || 0) - new Date(a.posted_datetime || 0);
  }).forEach(function (record) {
    const [postedDate, postedTime] = parsePostedDateTime(record.posted_datetime);
    const firstSeen = record.first_seen ? new Date(record.first_seen) : null;
    const lastSeen = record.last_seen ? new Date(record.last_seen) : null;
    let duration = '';

    if (firstSeen && lastSeen && !isNaN(firstSeen.getTime()) && !isNaN(lastSeen.getTime())) {
      const diffDays = (lastSeen.getTime() - firstSeen.getTime()) / 86400000;
      duration = diffDays.toFixed(2) + ' days';
    }

    rows.push([
      String(record.facility || ''),
      postedDate,
      postedTime,
      normalizeTags(record.category),
      String(record.message_text || ''),
      String(record.first_seen || ''),
      String(record.last_seen || ''),
      String(record.last_seen || ''),
      duration,
      sourceLabel(record.source_url)
    ]);
  });

  return rows;
}

function renderAppVsWebsiteRows(records) {
  const byId = {};

  records.forEach(function (record) {
    const id = String(record.message_id || '');
    if (!byId[id]) {
      byId[id] = [];
    }
    byId[id].push(record);
  });

  const rows = [];
  Object.keys(byId).sort().forEach(function (messageId) {
    const matching = byId[messageId];
    const representative = matching[0] || {};
    const sourceSet = matching.map(function (row) {
      return sourceLabel(row.source_url);
    });
    const [postedDate, postedTime] = parsePostedDateTime(representative.posted_datetime);
    const firstSeen = matching.map(function (row) { return row.first_seen || ''; }).filter(Boolean).sort()[0] || '';
    const lastSeen = matching.map(function (row) { return row.last_seen || ''; }).filter(Boolean).sort().slice(-1)[0] || '';

    rows.push([
      messageId,
      String(representative.facility || ''),
      [postedDate, postedTime].filter(Boolean).join(' '),
      sourceSet.includes('Website') ? 'TRUE' : 'FALSE',
      sourceSet.includes('Mobile API') ? 'TRUE' : 'FALSE',
      firstSeen,
      lastSeen,
      normalizeTags(representative.category),
      String(representative.message_text || '')
    ]);
  });

  return rows;
}

function buildDataDictionaryRows() {
  return [
    ['Status', 'Current lifecycle of the message: new, previous message still posted, updated, or cleared.'],
    ['Facility', 'Name of the reporting facility or site associated with the CAER message.'],
    ['Posted Date', 'The original CAER posting date from the source feed.'],
    ['Posted Time', 'The original CAER posting time from the source feed.'],
    ['Tags', 'Controlled CAER classification categories for filtering and review.'],
    ['Message', 'The complete CAER message text as published.'],
    ['First Seen', 'When the collector first observed the message.'],
    ['Last Seen', 'Most recent time the collector observed the message.'],
    ['Source', 'Where the message was observed: Website, Archive, or Mobile API.'],
    ['Previously Seen', 'Whether the current record was already observed earlier in the archive.'],
    ['Message ID', 'Stable identifier used to deduplicate duplicates and track message versions.']
  ];
}

function ensureSheets(spreadsheet) {
  const sheetNames = Object.keys(SHEET_LAYOUT);
  sheetNames.forEach(function (sheetName) {
    let sheet = spreadsheet.getSheetByName(sheetName);
    if (!sheet) {
      sheet = spreadsheet.insertSheet(sheetName);
    }
  });
}

function writeSheetData(spreadsheet, sheetName, headers, rows) {
  const sheet = spreadsheet.getSheetByName(sheetName);
  if (!sheet) {
    return;
  }

  sheet.clearContents();
  sheet.clearFormats();
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  }

  sheet.setFrozenRows(1);
  sheet.setFrozenColumns(0);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  sheet.autoResizeColumns(1, headers.length);
  sheet.setHiddenGridlines(true);
  sheet.getRange(1, 1, Math.max(sheet.getLastRow(), 1), headers.length).createFilter();
}

function refreshData() {
  createTimeTrigger();
  try {
    const response = UrlFetchApp.fetch(DATA_URL, {
      muteHttpExceptions: true,
      followRedirects: true
    });

    const statusCode = response.getResponseCode();
    if (statusCode !== 200) {
      throw new Error('GitHub data source returned HTTP ' + statusCode);
    }

    const payload = JSON.parse(response.getContentText('utf-8'));
    const records = Array.isArray(payload) ? payload : [];
    const spreadsheet = SpreadsheetApp.openById(TARGET_SHEET_ID);

    ensureSheets(spreadsheet);

    writeSheetData(spreadsheet, 'Current Messages', SHEET_LAYOUT['Current Messages'], renderCurrentRows(records));
    writeSheetData(spreadsheet, 'New Messages', SHEET_LAYOUT['New Messages'], renderNewRows(records));
    writeSheetData(spreadsheet, 'Still Posted', SHEET_LAYOUT['Still Posted'], renderStillPostedRows(records));
    writeSheetData(spreadsheet, 'Cleared Messages', SHEET_LAYOUT['Cleared Messages'], renderClearedRows(records));
    writeSheetData(spreadsheet, 'App vs Website', SHEET_LAYOUT['App vs Website'], renderAppVsWebsiteRows(records));
    writeSheetData(spreadsheet, 'Data Dictionary', SHEET_LAYOUT['Data Dictionary'], buildDataDictionaryRows());

    SpreadsheetApp.flush();
    return {status: 'success', count: records.length};
  } catch (error) {
    Logger.log('CAER Apps Script refresh failed: ' + error.message);
    SpreadsheetApp.getUi().alert('CAER refresh failed. The existing spreadsheet data was left unchanged because the GitHub source could not be retrieved.');
    return {status: 'error', message: error.message};
  }
}

function createTimeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  const exists = triggers.some(function (trigger) {
    return trigger.getHandlerFunction() === 'refreshData';
  });

  if (!exists) {
    ScriptApp.newTrigger('refreshData').timeBased().everyHours(18).create();
  }
}
