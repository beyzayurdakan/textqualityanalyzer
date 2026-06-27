const BASE_API_URL = "  ";

function postJson(path, payload) {
  const apiUrl = (BASE_API_URL || "").trim();

  if (!apiUrl) {
    return {
      success: false,
      message: "BASE_API_URL is empty. Please set the current ngrok URL in Code.gs."
    };
  }

  try {
    const response = UrlFetchApp.fetch(apiUrl + path, {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload || {}),
      muteHttpExceptions: true
    });

    const status = response.getResponseCode();
    const body = response.getContentText();

    if (status !== 200) {
      return {
        success: false,
        message: body || ("API request failed with HTTP " + status)
      };
    }

    return JSON.parse(body);
  } catch (error) {
    return {
      success: false,
      message: (
        "API connection failed. Check uvicorn, ngrok, and BASE_API_URL. " +
        "Details: " + error.message
      )
    };
  }
}



function onOpen() {
  DocumentApp.getUi()
    .createMenu("Writing Assistant")
    .addItem("Open Assistant", "showSidebar")
    .addToUi();
}

function showSidebar() {
  const html = HtmlService
    .createHtmlOutputFromFile("Sidebar")
    .setTitle("Writing Assistant");

  DocumentApp.getUi().showSidebar(html);
}

function getSelectedText() {
  const document = DocumentApp.getActiveDocument();
  const selection = document.getSelection();

  if (!selection) {
    return {
      success: false,
      message: "Please select text first."
    };
  }

  const rangeElements = selection.getRangeElements();
  let selectedText = "";

  rangeElements.forEach(function(rangeElement) {
    const element = rangeElement.getElement();

    if (element.editAsText) {
      const textElement = element.asText();

      if (rangeElement.isPartial()) {
        const start = rangeElement.getStartOffset();
        const end = rangeElement.getEndOffsetInclusive();

        selectedText += textElement
          .getText()
          .substring(start, end + 1);
      } else {
        selectedText += textElement.getText();
      }

      selectedText += "\n";
    }
  });

  return {
    success: true,
    text: selectedText.trim()
  };
}

function analyzeSelectedText() {
  const selected = getSelectedText();

  if (!selected.success) {
    return selected;
  }

  clearStoredReviewState();

  const result = postJson("/analyze", {
    text: selected.text
  });

  if (!result.success) {
    return result;
  }

  PropertiesService.getDocumentProperties().setProperty(
    "latestOriginalText",
    selected.text
  );

  PropertiesService.getDocumentProperties().setProperty(
    "latestAnalysisResult",
    JSON.stringify(result)
  );

  return result;
}

function clearStoredReviewState() {
  const props = PropertiesService.getDocumentProperties();
  props.deleteProperty("latestOriginalText");
  props.deleteProperty("latestAnalysisResult");
  props.deleteProperty("latestOptimizedText");

  return {
    success: true
  };
}

function rewriteAfterReview(mode, decisions) {
  
  const props = PropertiesService.getDocumentProperties();

  const originalText = props.getProperty("latestOriginalText");
  const latestAnalysisResult = props.getProperty("latestAnalysisResult");

  if (!originalText || !latestAnalysisResult) {
    return {
      success: false,
      message: "No successful analysis found. Please run analysis first."
    };
  }

  if (!originalText) {
    return {
      success: false,
      message: "No analyzed text found. Please run analysis first."
    };
  }

  const result = postJson("/rewrite", {
    text: originalText,
    mode: mode || "concise",
    decisions: decisions || {},
    analysis: JSON.parse(latestAnalysisResult)
  });

  if (!result.success) {
    return result;
  }

  PropertiesService.getDocumentProperties().setProperty(
    "latestOptimizedText",
    result.final || ""
  );

  return result;
}

function previewAfterReview(decisions) {
  const props = PropertiesService.getDocumentProperties();

  const originalText = props.getProperty("latestOriginalText");
  const latestAnalysisResult = props.getProperty("latestAnalysisResult");

  if (!originalText || !latestAnalysisResult) {
    return {
      success: false,
      message: "No successful analysis found. Please run analysis first."
    };
  }

  const result = postJson("/preview", {
    text: originalText,
    decisions: decisions || {},
    analysis: JSON.parse(latestAnalysisResult)
  });

  if (!result.success) {
    return result;
  }

  return result;
}

function applyReviewDecisionsToSelection(decisions) {
  const props = PropertiesService.getDocumentProperties();

  const originalText = props.getProperty("latestOriginalText");
  const latestAnalysisResult = props.getProperty("latestAnalysisResult");

  if (!originalText || !latestAnalysisResult) {
    return {
      success: false,
      message: "No successful analysis found. Please run analysis first."
    };
  }

  const result = postJson("/preview", {
    text: originalText,
    decisions: decisions || {},
    analysis: JSON.parse(latestAnalysisResult)
  });

  if (!result.success) {
    return result;
  }

  const replaceResult = replaceSelectedTextWith(result.final || "");

  if (!replaceResult.success) {
    return replaceResult;
  }

  result.message = "Document updated with selected review decisions.";
  return result;
}

function saveOptimizedTextFromSidebar(text) {
  PropertiesService.getDocumentProperties().setProperty(
    "latestOptimizedText",
    text || ""
  );

  return {
    success: true,
    message: "Optimized text saved."
  };
}

function replaceSelectedTextWith(replacementText) {
  if (!replacementText) {
    return {
      success: false,
      message: "No replacement text available."
    };
  }

  const document = DocumentApp.getActiveDocument();
  const selection = document.getSelection();

  if (!selection) {
    return {
      success: false,
      message: "Please select the original text again."
    };
  }

  const rangeElements = selection.getRangeElements();

  if (!rangeElements.length) {
    return {
      success: false,
      message: "No selected text found."
    };
  }

  const firstRangeElement = rangeElements[0];
  const firstTextElement = firstRangeElement.getElement().asText();
  const insertOffset = firstRangeElement.isPartial()
    ? firstRangeElement.getStartOffset()
    : 0;

  // Delete from the end of the selection backwards. This keeps offsets valid
  // even when the selected text spans multiple text nodes or paragraphs.
  for (let i = rangeElements.length - 1; i >= 0; i--) {
    const rangeElement = rangeElements[i];
    const textElement = rangeElement.getElement().asText();

    if (rangeElement.isPartial()) {
      textElement.deleteText(
        rangeElement.getStartOffset(),
        rangeElement.getEndOffsetInclusive()
      );
    } else {
      textElement.setText("");
    }
  }

  firstTextElement.insertText(insertOffset, replacementText);

  const endOffset = insertOffset + replacementText.length - 1;
  if (endOffset >= insertOffset) {
    const newRange = document
      .newRange()
      .addElement(firstTextElement, insertOffset, endOffset)
      .build();
    document.setSelection(newRange);
  }

  return {
    success: true,
    message: "Text replaced successfully."
  };
}

function acceptRewrite() {
  const optimizedText =
    PropertiesService.getDocumentProperties().getProperty(
      "latestOptimizedText"
    );

  if (!optimizedText) {
    return {
      success: false,
      message: "No optimized text available."
    };
  }

  const replaceResult = replaceSelectedTextWith(optimizedText);

  if (!replaceResult.success) {
    return replaceResult;
  }

  clearStoredReviewState();

  return {
    success: true,
    cleared: true,
    message: "Text replaced successfully. Analysis cleared."
  };
}
