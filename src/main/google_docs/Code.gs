function myFunction() {
  
}
// ============================================================
// Text Quality Analyzer - Google Docs Apps Script Backend
// ============================================================

//BACKEND URL SHOULD BE HERE
const SPACY_BACKEND_URL = 'url';

const LONG_SENTENCE_WORD_LIMIT = 30;
const SHORT_PARAGRAPH_WORD_LIMIT = 20;
const MANY_COMMAS_LIMIT = 4;

const SENTENCE_WARNING_BACKGROUND = '#fce5cd';
const REPETITION_BACKGROUND = '#ffff00';
const POSSIBLE_MISSPELLING_BACKGROUND = '#f4cccc';

const ORANGE_TEXT = '#e69138';
const NAVY_TEXT = '#073763';
const DARK_TEXT = '#202124';
const LIGHT_GRAY = '#f3f6f9';


// ============================================================
// Google Docs menu and sidebar
// ============================================================

function onOpen() {
  DocumentApp.getUi()
    .createMenu('Text Quality Analyzer')
    .addItem('Open analyzer', 'showSidebar')
    .addToUi();
}

function showSidebar() {
  const html = HtmlService
    .createHtmlOutputFromFile('Sidebar')
    .setTitle('Text Quality Analyzer');

  DocumentApp.getUi().showSidebar(html);
}


// ============================================================
// spaCy backend integration
// ============================================================

function getSpacyBackendBaseUrl_() {
  return SPACY_BACKEND_URL.replace(/\/$/, '');
}

function getSpacyRequestHeaders_() {
  return {
    'Accept': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  };
}

function parseJsonResponse_(response, contextLabel) {
  const statusCode = response.getResponseCode();
  const responseText = response.getContentText();

  if (statusCode !== 200) {
    throw new Error(
      contextLabel +
      ' failed. HTTP ' +
      statusCode +
      ': ' +
      responseText.substring(0, 500)
    );
  }

  try {
    return JSON.parse(responseText);
  } catch (error) {
    throw new Error(
      contextLabel +
      ' did not return JSON. First response characters: ' +
      responseText.substring(0, 300)
    );
  }
}

function analyzeWithSpacyBackend(targetAudiences) {
  const paragraphs = getDocumentParagraphs_();

  const fullText = paragraphs.map(function (paragraph) {
    return paragraph.text;
  }).join('\n\n');

  if (!fullText) {
    throw new Error('Document is empty.');
  }

  const payload = {
    text: fullText,
    paragraphs: paragraphs.map(function (paragraph) {
      return paragraph.text;
    }),
    target_audiences: normalizeTargetAudiences_(targetAudiences),
    long_sentence_word_limit: LONG_SENTENCE_WORD_LIMIT,
    low_gulpease_limit: 40,
    many_commas_limit: MANY_COMMAS_LIMIT,
    short_paragraph_word_limit: SHORT_PARAGRAPH_WORD_LIMIT
  };

  const response = UrlFetchApp.fetch(getSpacyBackendBaseUrl_() + '/analyze', {
    method: 'post',
    contentType: 'application/json',
    headers: getSpacyRequestHeaders_(),
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  return parseJsonResponse_(response, 'spaCy backend analysis');
}

function normalizeTargetAudiences_(targetAudiences) {
  if (!targetAudiences || !Array.isArray(targetAudiences) || targetAudiences.length === 0) {
    return ['general_public'];
  }

  return targetAudiences;
}

function getDocumentParagraphs_() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();

  return body.getParagraphs()
    .map(function (paragraph, index) {
      return {
        originalNumber: index + 1,
        text: paragraph.getText().trim()
      };
    })
    .filter(function (paragraph) {
      return paragraph.text.length > 0;
    })
    .map(function (paragraph, index) {
      return {
        number: index + 1,
        originalNumber: paragraph.originalNumber,
        text: paragraph.text
      };
    });
}


// ============================================================
// Select sentence or paragraph in Google Docs
// ============================================================

function selectSentenceInDocument(sentenceText) {
  if (!sentenceText || !sentenceText.trim()) {
    throw new Error('Sentence text is empty.');
  }

  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();

  const rangeInfo = findSentenceRangeInBody_(body, sentenceText);

  if (!rangeInfo) {
    throw new Error('Could not find this sentence in the document.');
  }

  const range = doc.newRange()
    .addElement(rangeInfo.textElement, rangeInfo.startOffset, rangeInfo.endOffset)
    .build();

  doc.setSelection(range);

  return {
    selected: true,
    type: 'sentence',
    preview: trimText_(sentenceText, 120)
  };
}

function selectParagraphInDocument(paragraphNumber) {
  const number = Number(paragraphNumber);

  if (!number || number < 1) {
    throw new Error('Invalid paragraph number.');
  }

  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const paragraphs = body.getParagraphs();

  let nonEmptyCount = 0;

  for (let i = 0; i < paragraphs.length; i++) {
    const textElement = paragraphs[i].editAsText();
    const text = textElement.getText();

    if (!text || text.trim().length === 0) {
      continue;
    }

    nonEmptyCount++;

    if (nonEmptyCount === number) {
      const range = doc.newRange()
        .addElement(textElement, 0, text.length - 1)
        .build();

      doc.setSelection(range);

      return {
        selected: true,
        type: 'paragraph',
        paragraphNumber: number,
        preview: trimText_(text, 120)
      };
    }
  }

  throw new Error('Could not find paragraph ' + number + ' in the document.');
}

function findSentenceRangeInBody_(body, sentenceText) {
  const target = normalizeTextForSelection_(sentenceText);
  const paragraphs = body.getParagraphs();

  for (let i = 0; i < paragraphs.length; i++) {
    const textElement = paragraphs[i].editAsText();
    const rawText = textElement.getText();

    const exactIndex = rawText.indexOf(sentenceText);

    if (exactIndex !== -1) {
      return {
        textElement: textElement,
        startOffset: exactIndex,
        endOffset: exactIndex + sentenceText.length - 1
      };
    }

    const mapped = normalizeWithOriginalIndexMap_(rawText);
    const normalizedIndex = mapped.normalizedText.indexOf(target);

    if (normalizedIndex !== -1) {
      const normalizedEndIndex = normalizedIndex + target.length - 1;

      return {
        textElement: textElement,
        startOffset: mapped.indexMap[normalizedIndex],
        endOffset: mapped.indexMap[normalizedEndIndex]
      };
    }
  }

  return null;
}

function normalizeTextForSelection_(text) {
  return String(text)
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeWithOriginalIndexMap_(rawText) {
  let normalizedText = '';
  const indexMap = [];
  let previousWasSpace = false;

  for (let i = 0; i < rawText.length; i++) {
    const char = rawText.charAt(i);
    const isSpace = /\s/.test(char);

    if (isSpace) {
      if (!previousWasSpace && normalizedText.length > 0) {
        normalizedText += ' ';
        indexMap.push(i);
      }

      previousWasSpace = true;
    } else {
      normalizedText += char;
      indexMap.push(i);
      previousWasSpace = false;
    }
  }

  if (normalizedText.endsWith(' ')) {
    normalizedText = normalizedText.slice(0, -1);
    indexMap.pop();
  }

  return {
    normalizedText: normalizedText,
    indexMap: indexMap
  };
}


// ============================================================
// Export analysis report
// ============================================================

function exportReportAsPdf(targetAudiences) {
  return exportAnalysisReport_('pdf', targetAudiences);
}

function exportReportAsDocx(targetAudiences) {
  return exportAnalysisReport_('docx', targetAudiences);
}

function exportAnalysisReport_(format, targetAudiences) {
  const sourceDoc = DocumentApp.getActiveDocument();
  const sourceFile = DriveApp.getFileById(sourceDoc.getId());
  const sourceName = sourceFile.getName();

  const result = analyzeWithSpacyBackend(targetAudiences);

  const timestamp = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    'yyyy-MM-dd_HH-mm'
  );

  const reportTitle = 'Text Quality Analysis Report - ' + sourceName + ' - ' + timestamp;

  const reportDoc = DocumentApp.create(reportTitle);
  const reportBody = reportDoc.getBody();

  buildImprovedReportDocument_(reportBody, result, sourceName);

  reportDoc.saveAndClose();

  let exportMimeType;
  let extension;
  let typeLabel;

  if (format === 'pdf') {
    exportMimeType = 'application/pdf';
    extension = 'pdf';
    typeLabel = 'PDF';
  } else if (format === 'docx') {
    exportMimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    extension = 'docx';
    typeLabel = 'DOCX';
  } else {
    throw new Error('Unsupported export format: ' + format);
  }

  const safeName = safeFileName_(reportTitle) + '.' + extension;
  const blob = exportGoogleDocAsBlob_(reportDoc.getId(), exportMimeType, safeName);
  const exportedFile = DriveApp.createFile(blob);

  DriveApp.getFileById(reportDoc.getId()).setTrashed(true);

  return {
    type: typeLabel,
    fileName: exportedFile.getName(),
    url: exportedFile.getUrl()
  };
}

function buildImprovedReportDocument_(body, result, sourceName) {
  body.clear();

  const title = body.appendParagraph('Text Quality Analysis Report');
  title.setHeading(DocumentApp.ParagraphHeading.HEADING1);
  styleParagraphText_(title, NAVY_TEXT, false, true);

  body.appendParagraph('Source document: ' + sourceName);
  body.appendParagraph('Generated at: ' + new Date().toLocaleString());

  appendReportSectionDivider_(body);

  appendReportLegend_(body);
  appendReportGlobalMetrics_(body, result);
  appendReportTargetAudienceAnalysis_(body, result);
  appendReportAnalysisOverview_(body, result);
  appendReportBaseVocabulary_(body, result);
  appendReportSentenceWarnings_(body, result);
  appendReportParagraphWarnings_(body, result);
  appendReportLemmaRepetitions_(body, result);
  appendNamedEntitySection_(body, result);
  appendReportNotes_(body, result);
}

function appendReportLegend_(body) {
  const heading = body.appendParagraph('Legend');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  appendStyledListItem_(body, 'Peach highlight: sentence-level readability or syntactic-complexity warning in the analyzed document.', DARK_TEXT, false);
  appendStyledListItem_(body, 'Yellow highlight: repeated lemma form detected by lemma-based repetition analysis.', DARK_TEXT, false);
  appendStyledListItem_(body, 'Pink highlight: possible misspelling or non-base vocabulary item.', DARK_TEXT, false);
  appendStyledListItem_(body, 'Orange italic bullets: sentence-level warnings and sentence metrics.', ORANGE_TEXT, true);
  appendStyledListItem_(body, 'Navy italic bullets: paragraph-level metrics and paragraph warnings.', NAVY_TEXT, true);

  appendReportSectionDivider_(body);
}

function appendReportGlobalMetrics_(body, result) {
  const metrics = result.global_metrics;

  const heading = body.appendParagraph('Global Analysis Summary');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const table = body.appendTable([
    ['Metric', 'Value'],
    ['Gulpease Index', formatNumber_(metrics.gulpease)],
    ['Readability', metrics.readability_label],
    ['Lexical Diversity Index', formatNumber_(metrics.lexical_diversity)],
    ['Syntactic Complexity Index', formatNumber_(metrics.syntactic_complexity_index)],
    ['Words', String(metrics.word_count)],
    ['Unique words', String(metrics.unique_word_count)],
    ['Sentences', String(metrics.sentence_count)],
    ['Letters', String(metrics.letter_count)]
  ]);

  styleReportTable_(table);
  appendReportSectionDivider_(body);
}

function appendReportTargetAudienceAnalysis_(body, result) {
  const heading = body.appendParagraph('Target Audience Analysis');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  if (!result.target_audience_analysis || result.target_audience_analysis.length === 0) {
    body.appendParagraph('No target audience analysis available.');
    appendReportSectionDivider_(body);
    return;
  }

  const rows = [[
    'Audience',
    'Overall fit',
    'Gulpease',
    'SCIX',
    'Base Vocabulary',
    'Recommended focus'
  ]];

  result.target_audience_analysis.forEach(function (item) {
    rows.push([
      item.label,
      item.overall_fit,
      item.gulpease_status + ' — ' + item.gulpease_interpretation,
      item.scix_status + ' — ' + item.scix_interpretation,
      item.base_vocabulary_status + ' — ' + item.base_vocabulary_interpretation,
      item.recommended_focus
    ]);
  });

  const table = body.appendTable(rows);
  styleReportTable_(table);
  appendReportSectionDivider_(body);
}

function appendReportAnalysisOverview_(body, result) {
  const heading = body.appendParagraph('Analysis Overview');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const items = result.analysis_overview || result.suggestions || [];

  if (items.length === 0) {
    body.appendParagraph('No major analysis overview items were generated.');
  } else {
    items.forEach(function (item) {
      appendStyledListItem_(body, normalizePluralText_(item), DARK_TEXT, false);
    });
  }

  appendReportSectionDivider_(body);
}

function appendReportBaseVocabulary_(body, result) {
  const heading = body.appendParagraph('Base Vocabulary Analysis');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const base = result.base_vocabulary;

  if (!base || !base.available) {
    body.appendParagraph(base && base.message ? base.message : 'Base Vocabulary analysis is unavailable.');
    appendReportSectionDivider_(body);
    return;
  }

  const summaryTable = body.appendTable([
    ['Metric', 'Value'],
    ['Vocabulary size', String(base.vocabulary_size)],
    ['Coverage', formatNumber_(base.coverage_percentage) + '%'],
    ['Checked tokens', String(base.checked_token_count)],
    ['Covered tokens', String(base.covered_token_count)],
    ['Outside tokens', String(base.outside_token_count)]
  ]);

  styleReportTable_(summaryTable);

  if (base.possible_misspellings && base.possible_misspellings.length > 0) {
    body.appendParagraph('Possible Misspellings / Non-Base Vocabulary')
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    const rows = [['Lemma', 'Count', 'Forms']];

    base.possible_misspellings.slice(0, 25).forEach(function (item) {
      const forms = item.forms
        ? item.forms.map(function (form) {
            return form.form + ' (' + form.count + ')';
          }).join(', ')
        : '';

      rows.push([item.lemma, String(item.count), forms]);
    });

    const table = body.appendTable(rows);
    styleReportTable_(table);
  }

  appendReportSectionDivider_(body);
}

function appendReportSentenceWarnings_(body, result) {
  const heading = body.appendParagraph('Sentence-Level Warnings');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const warningSentences = getWarningSentencesFromResult_(result);

  if (warningSentences.length === 0) {
    body.appendParagraph('No sentence-level warnings detected.');
    appendReportSectionDivider_(body);
    return;
  }

  warningSentences.forEach(function (sentence) {
    const sentenceTitle = body.appendParagraph('Sentence ' + sentence.number);
    sentenceTitle.setHeading(DocumentApp.ParagraphHeading.HEADING3);
    styleParagraphText_(sentenceTitle, ORANGE_TEXT, false, true);

    body.appendParagraph(sentence.text);

    sentence.warnings.forEach(function (warning) {
      appendStyledListItem_(body, normalizePluralText_(warning), ORANGE_TEXT, true);
    });

    appendStyledListItem_(body, 'Gulpease Index: ' + formatNumber_(sentence.gulpease), ORANGE_TEXT, true);
    appendStyledListItem_(body, 'Lexical Diversity Index: ' + formatNumber_(sentence.lexical_diversity), ORANGE_TEXT, true);
    appendStyledListItem_(body, 'Syntactic Complexity Index: ' + formatNumber_(sentence.syntactic_complexity_index), ORANGE_TEXT, true);
  });

  appendReportSectionDivider_(body);
}

function appendReportParagraphWarnings_(body, result) {
  const heading = body.appendParagraph('Paragraph-Level Warnings');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const paragraphWarnings = getParagraphWarningsFromResult_(result);

  if (paragraphWarnings.length === 0) {
    body.appendParagraph('No paragraph-level warnings detected.');
    appendReportSectionDivider_(body);
    return;
  }

  paragraphWarnings.forEach(function (paragraph) {
    const paragraphTitle = body.appendParagraph('Paragraph ' + paragraph.number);
    paragraphTitle.setHeading(DocumentApp.ParagraphHeading.HEADING3);
    styleParagraphText_(paragraphTitle, NAVY_TEXT, false, true);

    body.appendParagraph(paragraph.preview);

    appendStyledListItem_(body, 'Paragraph Gulpease Index: ' + formatNumber_(paragraph.gulpease), NAVY_TEXT, true);
    appendStyledListItem_(body, 'Paragraph Lexical Diversity Index: ' + formatNumber_(paragraph.lexical_diversity), NAVY_TEXT, true);
    appendStyledListItem_(body, 'Paragraph Syntactic Complexity Index: ' + formatNumber_(paragraph.syntactic_complexity_index), NAVY_TEXT, true);

    paragraph.warnings.forEach(function (warning) {
      appendStyledListItem_(body, normalizePluralText_(warning), NAVY_TEXT, true);
    });
  });

  appendReportSectionDivider_(body);
}

function appendReportLemmaRepetitions_(body, result) {
  const heading = body.appendParagraph('Lemma-Based Repetitions');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  if (!result.lemma_repetitions || result.lemma_repetitions.length === 0) {
    body.appendParagraph('No repeated lemmas detected.');
    appendReportSectionDivider_(body);
    return;
  }

  const rows = [['Lemma', 'Count', 'Forms']];

  result.lemma_repetitions.forEach(function (item) {
    const forms = item.forms
      ? item.forms.map(function (form) {
          return form.form + ' (' + form.count + ')';
        }).join(', ')
      : '';

    rows.push([
      item.lemma,
      String(item.count),
      forms
    ]);
  });

  const table = body.appendTable(rows);
  styleReportTable_(table);

  appendReportSectionDivider_(body);
}

function appendReportNotes_(body, result) {
  const heading = body.appendParagraph('Notes');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  if (result.notes && result.notes.purpose) {
    body.appendParagraph(result.notes.purpose);
  }

  if (result.notes && result.notes.base_vocabulary) {
    body.appendParagraph(result.notes.base_vocabulary);
  }

  if (result.notes && result.notes.target_audience) {
    body.appendParagraph(result.notes.target_audience);
  }

  if (result.notes && result.notes.syntactic_complexity_index) {
    body.appendParagraph(result.notes.syntactic_complexity_index);
  }
}

function exportGoogleDocAsBlob_(fileId, mimeType, fileName) {
  const url =
    'https://www.googleapis.com/drive/v3/files/' +
    encodeURIComponent(fileId) +
    '/export?mimeType=' +
    encodeURIComponent(mimeType);

  const response = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: {
      Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
    },
    muteHttpExceptions: true
  });

  const responseCode = response.getResponseCode();

  if (responseCode !== 200) {
    throw new Error(
      'Export failed. HTTP ' +
      responseCode +
      ': ' +
      response.getContentText()
    );
  }

  return response.getBlob().setName(fileName);
}


// ============================================================
// Get analyzed document
// ============================================================

function createAnalyzedDocument(targetAudiences) {
  const sourceDoc = DocumentApp.getActiveDocument();
  const sourceFile = DriveApp.getFileById(sourceDoc.getId());
  const sourceName = sourceFile.getName();

  const result = analyzeWithSpacyBackend(targetAudiences);
  const paragraphs = getDocumentParagraphs_();

  const sentenceMap = mapSentencesToParagraphs_(paragraphs, result.sentence_analysis || []);
  const repeatedForms = getRepeatedFormsFromResult_(result);
  const possibleMisspellingForms = getPossibleMisspellingFormsFromResult_(result);

  const timestamp = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    'yyyy-MM-dd_HH-mm'
  );

  const docTitle = 'Analyzed Document - ' + sourceName + ' - ' + timestamp;
  const analyzedDoc = DocumentApp.create(docTitle);
  const body = analyzedDoc.getBody();

  body.clear();

  const title = body.appendParagraph('Analyzed Document');
  title.setHeading(DocumentApp.ParagraphHeading.HEADING1);
  styleParagraphText_(title, NAVY_TEXT, false, true);

  body.appendParagraph('Source document: ' + sourceName);
  body.appendParagraph('Generated at: ' + new Date().toLocaleString());

  appendAnalyzedDocumentLegend_(body);
  appendGlobalAnalysisSummary_(body, result);
  appendAnalyzedDocumentTargetAudienceAnalysis_(body, result);
  appendAnalysisOverview_(body, result);
  appendAnalyzedDocumentBaseVocabulary_(body, result);

  paragraphs.forEach(function (paragraph) {
    appendAnalyzedParagraph_(body, paragraph, result, sentenceMap, repeatedForms, possibleMisspellingForms);
  });

  appendAnalyzedDocumentLemmaRepetitions_(body, result);
  appendNamedEntitySection_(body, result);

  analyzedDoc.saveAndClose();

  const analyzedFile = DriveApp.getFileById(analyzedDoc.getId());

  return {
    fileName: analyzedFile.getName(),
    url: analyzedFile.getUrl()
  };
}

function appendAnalyzedDocumentLegend_(body) {
  const heading = body.appendParagraph('Legend');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const peachItem = appendStyledListItem_(body, 'Peach highlight: sentence-level readability or syntactic-complexity warning.', DARK_TEXT, false);
  setListItemBackgroundSample_(peachItem, 'Peach highlight', SENTENCE_WARNING_BACKGROUND);

  const yellowItem = appendStyledListItem_(body, 'Yellow highlight: repeated lemma form.', DARK_TEXT, false);
  setListItemBackgroundSample_(yellowItem, 'Yellow highlight', REPETITION_BACKGROUND);

  const pinkItem = appendStyledListItem_(body, 'Pink highlight: possible misspelling or non-base vocabulary item.', DARK_TEXT, false);
  setListItemBackgroundSample_(pinkItem, 'Pink highlight', POSSIBLE_MISSPELLING_BACKGROUND);

  appendStyledListItem_(body, 'Orange italic bullets: sentence-level warnings and sentence metrics.', ORANGE_TEXT, true);
  appendStyledListItem_(body, 'Navy italic bullets: paragraph-level metrics and paragraph warnings.', NAVY_TEXT, true);

  body.appendParagraph('');
}

function appendGlobalAnalysisSummary_(body, result) {
  const metrics = result.global_metrics;

  const heading = body.appendParagraph('Global Analysis Summary');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  appendStyledListItem_(body, 'Gulpease Index: ' + formatNumber_(metrics.gulpease), NAVY_TEXT, true);
  appendStyledListItem_(body, 'Lexical Diversity Index: ' + formatNumber_(metrics.lexical_diversity), NAVY_TEXT, true);
  appendStyledListItem_(body, 'Syntactic Complexity Index: ' + formatNumber_(metrics.syntactic_complexity_index), NAVY_TEXT, true);
  appendStyledListItem_(body, 'Readability: ' + metrics.readability_label, NAVY_TEXT, true);

  body.appendParagraph('');
}

function appendAnalyzedDocumentTargetAudienceAnalysis_(body, result) {
  const heading = body.appendParagraph('Target Audience Analysis');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  if (!result.target_audience_analysis || result.target_audience_analysis.length === 0) {
    body.appendParagraph('No target audience analysis available.');
    body.appendParagraph('');
    return;
  }

  const rows = [[
    'Audience',
    'Overall fit',
    'Gulpease',
    'SCIX',
    'Base Vocabulary'
  ]];

  result.target_audience_analysis.forEach(function (item) {
    rows.push([
      item.label,
      item.overall_fit,
      item.gulpease_status,
      item.scix_status,
      item.base_vocabulary_status
    ]);
  });

  const table = body.appendTable(rows);
  styleReportTable_(table);

  result.target_audience_analysis.forEach(function (item) {
    appendStyledListItem_(body, item.label + ': ' + item.recommended_focus, DARK_TEXT, false);
  });

  body.appendParagraph('');
}

function appendAnalysisOverview_(body, result) {
  const heading = body.appendParagraph('Analysis Overview');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const items = result.analysis_overview || result.suggestions || [];

  if (items.length === 0) {
    body.appendParagraph('No major analysis overview items were generated.');
    body.appendParagraph('');
    return;
  }

  items.forEach(function (item) {
    appendStyledListItem_(body, normalizePluralText_(item), DARK_TEXT, false);
  });

  body.appendParagraph('');
}

function appendAnalyzedDocumentBaseVocabulary_(body, result) {
  const heading = body.appendParagraph('Base Vocabulary Analysis');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  const base = result.base_vocabulary;

  if (!base || !base.available) {
    body.appendParagraph(base && base.message ? base.message : 'Base Vocabulary analysis is unavailable.');
    body.appendParagraph('');
    return;
  }

  appendStyledListItem_(body, 'Base Vocabulary coverage: ' + formatNumber_(base.coverage_percentage) + '%', DARK_TEXT, false);
  appendStyledListItem_(body, 'Checked tokens: ' + base.checked_token_count, DARK_TEXT, false);
  appendStyledListItem_(body, 'Outside tokens: ' + base.outside_token_count, DARK_TEXT, false);

  if (base.possible_misspellings && base.possible_misspellings.length > 0) {
    body.appendParagraph('Possible Misspellings / Non-Base Vocabulary')
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    base.possible_misspellings.slice(0, 20).forEach(function (item) {
      const forms = item.forms
        ? item.forms.map(function (form) {
            return form.form + ' (' + form.count + ')';
          }).join(', ')
        : '';

      appendStyledListItem_(body, item.lemma + ': ' + item.count + ' ' + pluralWord_(item.count, 'time', 'times') + (forms ? ' — Forms: ' + forms : ''), DARK_TEXT, false);
    });
  }

  body.appendParagraph('');
}

function appendAnalyzedParagraph_(body, paragraph, result, sentenceMap, repeatedForms, possibleMisspellingForms) {
  const paragraphAnalysis = findParagraphAnalysis_(result, paragraph.number);
  const sentenceItems = sentenceMap[paragraph.number] || [];

  const title = body.appendParagraph('Paragraph ' + paragraph.number);
  styleParagraphText_(title, NAVY_TEXT, true, false);

  if (sentenceItems.length === 0) {
    const fallbackParagraph = body.appendParagraph(paragraph.text);
    const textElement = fallbackParagraph.editAsText();
    applyPossibleMisspellingBackgrounds_(textElement, paragraph.text, possibleMisspellingForms);
    applyRepeatedFormBackgrounds_(textElement, paragraph.text, repeatedForms);
  } else {
    sentenceItems.forEach(function (sentence) {
      appendAnalyzedSentence_(body, sentence, repeatedForms, possibleMisspellingForms);
    });
  }

  if (paragraphAnalysis) {
    appendParagraphMetrics_(body, paragraphAnalysis);
  }

  body.appendParagraph('');
}

function appendAnalyzedSentence_(body, sentence, repeatedForms, possibleMisspellingForms) {
  const sentenceParagraph = body.appendParagraph(sentence.text);
  const textElement = sentenceParagraph.editAsText();

  if (sentence.warnings && sentence.warnings.length > 0) {
    setTextBackground_(textElement, SENTENCE_WARNING_BACKGROUND);
  }

  applyPossibleMisspellingBackgrounds_(textElement, sentence.text, possibleMisspellingForms);
  applyRepeatedFormBackgrounds_(textElement, sentence.text, repeatedForms);

  if (sentence.warnings && sentence.warnings.length > 0) {
    appendSentenceMetricsAndWarnings_(body, sentence);
  }
}

function appendSentenceMetricsAndWarnings_(body, sentence) {
  sentence.warnings.forEach(function (warning) {
    appendStyledListItem_(body, normalizePluralText_(warning), ORANGE_TEXT, true);
  });

  appendStyledListItem_(body, 'Gulpease Index: ' + formatNumber_(sentence.gulpease), ORANGE_TEXT, true);
  appendStyledListItem_(body, 'Lexical Diversity Index: ' + formatNumber_(sentence.lexical_diversity), ORANGE_TEXT, true);
  appendStyledListItem_(body, 'Syntactic Complexity Index: ' + formatNumber_(sentence.syntactic_complexity_index), ORANGE_TEXT, true);
}

function appendParagraphMetrics_(body, paragraphAnalysis) {
  appendStyledListItem_(body, 'Paragraph Gulpease Index: ' + formatNumber_(paragraphAnalysis.gulpease), NAVY_TEXT, true);
  appendStyledListItem_(body, 'Paragraph Lexical Diversity Index: ' + formatNumber_(paragraphAnalysis.lexical_diversity), NAVY_TEXT, true);
  appendStyledListItem_(body, 'Paragraph Syntactic Complexity Index: ' + formatNumber_(paragraphAnalysis.syntactic_complexity_index), NAVY_TEXT, true);

  if (paragraphAnalysis.warnings && paragraphAnalysis.warnings.length > 0) {
    paragraphAnalysis.warnings.forEach(function (warning) {
      appendStyledListItem_(body, normalizePluralText_(warning), NAVY_TEXT, true);
    });
  }
}

function appendAnalyzedDocumentLemmaRepetitions_(body, result) {
  const heading = body.appendParagraph('Lemma-Based Repetitions');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  if (!result.lemma_repetitions || result.lemma_repetitions.length === 0) {
    body.appendParagraph('No repeated lemmas detected.');
    body.appendParagraph('');
    return;
  }

  result.lemma_repetitions.forEach(function (item) {
    const forms = item.forms
      ? item.forms.map(function (form) {
          return form.form + ' (' + form.count + ')';
        }).join(', ')
      : '';

    const text = item.lemma +
      ': ' +
      item.count +
      ' ' +
      pluralWord_(item.count, 'time', 'times') +
      (forms ? ' — Forms: ' + forms : '');

    appendStyledListItem_(body, text, DARK_TEXT, false);
  });

  body.appendParagraph('');
}

function appendNamedEntitySection_(body, result) {
  const heading = body.appendParagraph('Named Entities');
  heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);
  styleParagraphText_(heading, NAVY_TEXT, false, true);

  if (
    !result.named_entities ||
    !result.named_entities.grouped_by_label ||
    Object.keys(result.named_entities.grouped_by_label).length === 0
  ) {
    body.appendParagraph('No named entities detected.');
    return;
  }

  const grouped = result.named_entities.grouped_by_label;
  const labels = Object.keys(grouped).sort();

  labels.forEach(function (label) {
    const entities = grouped[label];

    const labelHeading = body.appendParagraph(label);
    labelHeading.setHeading(DocumentApp.ParagraphHeading.HEADING3);
    styleParagraphText_(labelHeading, NAVY_TEXT, false, true);

    entities.forEach(function (entity) {
      body.appendListItem(
        entity.text +
        ' — ' +
        entity.count +
        ' ' +
        pluralWord_(entity.count, 'time', 'times') +
        ' — ' +
        (entity.description || label)
      );
    });
  });
}


// ============================================================
// Mapping helpers
// ============================================================

function mapSentencesToParagraphs_(paragraphs, sentenceAnalysis) {
  const map = {};

  paragraphs.forEach(function (paragraph) {
    map[paragraph.number] = [];
  });

  sentenceAnalysis.forEach(function (sentence) {
    const sentenceText = normalizeTextForSelection_(sentence.text);

    for (let i = 0; i < paragraphs.length; i++) {
      const paragraph = paragraphs[i];
      const paragraphText = normalizeTextForSelection_(paragraph.text);

      if (paragraphText.indexOf(sentenceText) !== -1) {
        map[paragraph.number].push(sentence);
        return;
      }
    }
  });

  return map;
}

function findParagraphAnalysis_(result, paragraphNumber) {
  if (!result.paragraph_analysis) {
    return null;
  }

  for (let i = 0; i < result.paragraph_analysis.length; i++) {
    if (Number(result.paragraph_analysis[i].number) === Number(paragraphNumber)) {
      return result.paragraph_analysis[i];
    }
  }

  return null;
}


// ============================================================
// Shared helpers
// ============================================================

function getWarningSentencesFromResult_(result) {
  if (!result || !result.sentence_analysis) {
    return [];
  }

  return result.sentence_analysis.filter(function (sentence) {
    return sentence.warnings && sentence.warnings.length > 0;
  });
}

function getParagraphWarningsFromResult_(result) {
  if (!result || !result.paragraph_analysis) {
    return [];
  }

  return result.paragraph_analysis.filter(function (paragraph) {
    return paragraph.warnings && paragraph.warnings.length > 0;
  });
}

function getRepeatedFormsFromResult_(result) {
  const forms = {};

  if (!result || !result.lemma_repetitions) {
    return [];
  }

  result.lemma_repetitions.forEach(function (item) {
    if (!item.forms) {
      return;
    }

    item.forms.forEach(function (formItem) {
      if (formItem.form && formItem.form.length >= 4) {
        forms[formItem.form.toLowerCase()] = true;
      }
    });
  });

  return Object.keys(forms);
}

function getPossibleMisspellingFormsFromResult_(result) {
  const forms = {};

  if (!result || !result.base_vocabulary || !result.base_vocabulary.possible_misspellings) {
    return [];
  }

  result.base_vocabulary.possible_misspellings.forEach(function (item) {
    if (!item.forms) {
      return;
    }

    item.forms.forEach(function (formItem) {
      if (formItem.form && formItem.form.length >= 4) {
        forms[formItem.form.toLowerCase()] = true;
      }
    });
  });

  return Object.keys(forms);
}

function applyRepeatedFormBackgrounds_(textElement, sourceText, repeatedForms) {
  repeatedForms.forEach(function (form) {
    const ranges = findWordRanges_(sourceText, form);

    ranges.forEach(function (range) {
      try {
        textElement.setBackgroundColor(range.start, range.end, REPETITION_BACKGROUND);
      } catch (error) {
        Logger.log('Could not highlight repeated form "' + form + '": ' + error.message);
      }
    });
  });
}

function applyPossibleMisspellingBackgrounds_(textElement, sourceText, possibleMisspellingForms) {
  possibleMisspellingForms.forEach(function (form) {
    const ranges = findWordRanges_(sourceText, form);

    ranges.forEach(function (range) {
      try {
        textElement.setBackgroundColor(range.start, range.end, POSSIBLE_MISSPELLING_BACKGROUND);
      } catch (error) {
        Logger.log('Could not highlight possible misspelling "' + form + '": ' + error.message);
      }
    });
  });
}

function findWordRanges_(text, word) {
  const ranges = [];
  const escapedWord = escapeRegex_(word);

  const regex = new RegExp(
    '(^|[^A-Za-zÀ-ÖØ-öø-ÿ])(' + escapedWord + ')(?=$|[^A-Za-zÀ-ÖØ-öø-ÿ])',
    'gi'
  );

  let match;

  while ((match = regex.exec(text)) !== null) {
    const prefixLength = match[1] ? match[1].length : 0;
    const start = match.index + prefixLength;
    const end = start + match[2].length - 1;

    ranges.push({
      start: start,
      end: end
    });
  }

  return ranges;
}

function setTextBackground_(textElement, color) {
  const value = textElement.getText();

  if (!value || value.length === 0) {
    return;
  }

  textElement.setBackgroundColor(0, value.length - 1, color);
}

function setListItemBackgroundSample_(listItem, sampleText, color) {
  const text = listItem.editAsText();
  const value = text.getText();
  const start = value.indexOf(sampleText);

  if (start === -1) {
    return;
  }

  const end = start + sampleText.length - 1;
  text.setBackgroundColor(start, end, color);
}

function appendStyledListItem_(body, text, color, italic) {
  const item = body.appendListItem(text);
  item.setGlyphType(DocumentApp.GlyphType.BULLET);
  styleParagraphText_(item, color, italic, false);
  return item;
}

function styleParagraphText_(paragraph, color, italic, bold) {
  const text = paragraph.editAsText();
  const value = text.getText();

  if (!value || value.length === 0) {
    return;
  }

  const start = 0;
  const end = value.length - 1;

  if (color) {
    text.setForegroundColor(start, end, color);
  }

  text.setItalic(start, end, !!italic);
  text.setBold(start, end, !!bold);
}

function styleReportTable_(table) {
  const header = table.getRow(0);

  for (let i = 0; i < header.getNumCells(); i++) {
    const cell = header.getCell(i);
    cell.setBackgroundColor(LIGHT_GRAY);
    const text = cell.editAsText();
    const value = text.getText();

    if (value && value.length > 0) {
      text.setBold(0, value.length - 1, true);
    }
  }
}

function appendReportSectionDivider_(body) {
  body.appendParagraph('');
}

function escapeRegex_(text) {
  return String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function pluralWord_(count, singular, plural) {
  return Number(count) === 1 ? singular : plural;
}

function normalizePluralText_(text) {
  return String(text)
    .replace(/\b1 sentence\(s\)/g, '1 sentence')
    .replace(/\b([2-9]\d*|0) sentence\(s\)/g, '$1 sentences')
    .replace(/\b1 paragraph\(s\)/g, '1 paragraph')
    .replace(/\b([2-9]\d*|0) paragraph\(s\)/g, '$1 paragraphs')
    .replace(/\b1 word\(s\)/g, '1 word')
    .replace(/\b([2-9]\d*|0) word\(s\)/g, '$1 words')
    .replace(/\b1 time\(s\)/g, '1 time')
    .replace(/\b([2-9]\d*|0) time\(s\)/g, '$1 times')
    .replace(/\(s\)/g, 's');
}

function trimText_(text, maxLength) {
  if (!text) {
    return '';
  }

  const clean = String(text).replace(/\s+/g, ' ').trim();

  if (clean.length <= maxLength) {
    return clean;
  }

  return clean.substring(0, maxLength - 3) + '...';
}

function formatNumber_(value) {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  return String(value);
}

function safeFileName_(name) {
  return name
    .replace(/[\\/:*?"<>|#%{}~&]/g, '-')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 180);
}
