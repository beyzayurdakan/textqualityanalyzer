# References and Research Notes — Italian Text Quality Analyzer

## Purpose of this file

This document collects research notes for the **Italian Text Quality Analyzer** project and provides a literature review, an analysis of the existing prototype, and research-based extension ideas.
It is intended to support the early requirement-engineering phase, before deciding the final implementation.

The document has three goals:

1. to formulate meaningful research questions about text quality analysis;
2. to answer those questions using relevant papers, tools, and existing projects;
3. to analyze the existing SE-25 Text Quality Evaluator prototype and identify how it could be extended in a research-based way.

This is not a final requirement specification. It is a research-oriented reference document that can later support the URS, SRS, design documentation, and implementation plan.

---

# 1. Research Questions and Evidence-Based Answers

## Q1. What does “text quality” mean in the context of an automatic analyzer?

Text quality is not a single measurable property. It is a combination of readability, lexical choice, syntactic structure, cohesion, discourse organization, spelling and grammar correctness, and the relationship between the text and its intended audience.

A text may be grammatically correct but difficult to read. Another text may be simple and readable but stylistically poor or repetitive. For this reason, a text quality analyzer should not only return one global score. It should provide multiple indicators that help users understand different dimensions of quality.

Research on readability and text quality supports this multi-dimensional view. Pitler and Nenkova combine lexical, syntactic, and discourse features to predict human judgments of readability and text quality, showing that perceived quality depends on more than simple surface measures [R1]. Coh-Metrix follows a similar idea by analyzing text through multiple measures of cohesion, language, and readability [R2].

For our project, this means that “quality” should be treated as a set of partial observations rather than a final judgment.

---

## Q2. Why is a single readability formula not enough?

Traditional readability formulas are useful because they are simple, fast, and interpretable. However, they usually rely on a small number of surface features, such as sentence length, word length, or syllable count. These features are only rough approximations of the linguistic factors that affect reading difficulty.

Pitler and Nenkova explicitly discuss that standard readability indices use only a few simple factors and are rough approximations of the linguistic elements that determine readability [R1]. Petersen and Ostendorf also explain that traditional measures may fail when texts contain difficult topic-specific vocabulary but relatively simple sentence structures, or the opposite situation [R3].

This does not mean that readability formulas are useless. It means that they should be used as one component of a broader analysis. For an Italian text quality analyzer, a formula such as Gulpease can be an important first indicator, but it should be complemented with lexical, syntactic, and discourse-level information.

---

## Q3. Why is Italian-specific readability analysis necessary?

Readability is language-dependent. A formula designed for English cannot be directly transferred to Italian without considering differences in morphology, syntax, word length, sentence structure, and educational context.

For Italian, the **Gulpease Index** is especially relevant because it was designed specifically for Italian texts [R4]. In addition, READ-IT was developed as an advanced readability assessment tool for Italian and combines raw text features with lexical, morpho-syntactic, and syntactic information [R5].

This is important for our project because the analyzer must work on Italian texts. Therefore, Italian-specific formulas, Italian vocabulary resources, and Italian NLP tools should be preferred over English-only solutions.

---

## Q4. Why is the Gulpease Index useful, and what are its limitations?

The Gulpease Index is useful because it is simple, interpretable, and designed for Italian. It is based on the number of letters, words, and sentences. A higher Gulpease score generally means that the text is easier to read.

Its main advantage is that it gives a quick readability estimate without requiring complex NLP processing. This makes it appropriate as a baseline metric. In the existing prototype, Gulpease is also interpreted through three educational levels: elementary school, middle school, and high school. This is important because readability is not absolute; the same text can be easy for one reader group and difficult for another.

However, Gulpease still has limitations. It does not directly measure cohesion, discourse structure, entity continuity, vocabulary frequency, ambiguity of the text. A text can obtain an acceptable Gulpease score and still be weak because of poor cohesion, repetitions, unclear references, or inconsistent narrative structure.

For this reason, Gulpease should be preserved as a baseline, but it should not be treated as the complete definition of text quality.

---

## Q5. Why do lexical features matter in text quality analysis?

Lexical features are important because vocabulary affects how easily readers understand a text. Rare words, technical terminology, excessive repetition, poor lexical variety, and inappropriate word choice can all influence readability and perceived quality.

Pitler and Nenkova show that vocabulary-based features are significantly associated with readability judgments in their experiments [R1]. Petersen and Ostendorf also use language-model features and traditional reading-level measures to improve reading-level assessment [R3].

For Italian text analysis, lexical features could include:

- lexical diversity;
- frequency of rare words;
- use of basic vocabulary;
- repeated terms or expressions;
- content-word density;
- type-token ratio or more robust lexical diversity measures;
- lemma-based repetition rather than only exact-word repetition.

This is directly relevant because the existing prototype already calculates a lexical diversity index and checks whether words belong to the Italian base vocabulary.

---

## Q6. Why is lexical diversity alone not sufficient?

Lexical diversity measures the variety of words in a text, but it can be misleading if used alone. A high lexical diversity score does not automatically mean that the text is better. For example, a text may use many different words but still be unclear, inconsistent, or stylistically inappropriate.

Simple type-token ratio is also sensitive to text length: short texts often appear more diverse because there are fewer repeated words. For longer texts, repeated function words and topic-related terms naturally reduce the score.

Therefore, lexical diversity should be interpreted carefully. It should be combined with other indicators such as readability, sentence complexity, repetition patterns, vocabulary frequency, and cohesion.

---

## Q7. Why should syntactic complexity be measured?

Syntactic complexity is relevant because complex sentence structures can increase processing difficulty. Long sentences, multiple subordinate clauses, embedded phrases, and unclear syntactic dependencies can make a text harder to read.

Petersen and Ostendorf combine parse-based features with language-model and traditional readability features in reading-level assessment [R3]. READ-IT also includes syntactic information as part of Italian readability assessment [R5].

For our project, syntactic complexity can support warnings such as:

- very long sentences;
- high number of subordinate clauses;
- complex dependency structures;
- excessive clause embedding;
- sentence structures that may be hard to parse.

However, syntactic complexity is not always negative. Literary Italian may intentionally use long or complex sentences. Therefore, the system should report syntactic complexity as an indicator, not as an automatic error.

---

## Q8. Why are local readability analyses important?

Document-level scores are useful, but they do not tell the user exactly where the problem is. If a long text receives a low readability score, the user still needs to know which part of the document contributes to the problem.

READ-IT explicitly evaluates readability both at document level and sentence level, and this is important for connecting readability assessment with text simplification [R5]. Aluísio et al. also discuss readability assessment as a function inside a text simplification authoring tool, where users need feedback on how their choices affect readability [R6].

The existing prototype already supports **paragraph-level** Gulpease analysis. This is a strong point because the user can compare the readability of different paragraphs instead of relying only on a global score. A natural improvement would be to extend this local analysis further by identifying difficult sentences inside each paragraph and explaining why they are difficult.

---

## Q9. Why should discourse and cohesion be considered in text quality analysis?

A text can be grammatically correct and still feel incoherent. Cohesion and discourse organization help readers understand how sentences connect, how topics develop, and how information flows.

Pitler and Nenkova show that discourse relations are strongly associated with perceived text quality and that discourse features can be robust across different readability prediction tasks [R1]. Coh-Metrix also measures text at multiple levels, including cohesion and language features [R2].

For a narrative or editorial assistant, cohesion-related indicators may include:

- continuity of main entities or characters;
- abrupt topic shifts;
- repeated or missing connectives;
- paragraph transitions;
- balance between explicit and implicit relations;
- consistency of references to characters, places, or concepts.

This area is more difficult than counting words or sentences, but it is important for a richer concept of text quality.

---

## Q10. Why is the intended audience important?

The same text can be appropriate for one audience and too difficult for another. A scientific article, a children’s story, a literary novel, and a public information text have different expectations.

Pitler and Nenkova state that readability depends strongly on the intended readers [R1]. Petersen and Ostendorf also discuss reading-level assessment in the context of finding appropriate materials for learners, where vocabulary and syntactic complexity may affect different groups differently [R3].

The existing prototype already contains a basic form of audience-aware interpretation: it compares Gulpease readability against elementary school, middle school, and high school levels. This is useful because the same text can be easy for one educational level and hard for another.

However, this is still a fixed interpretation model. The system does not currently allow users to define a custom target audience, genre, or text purpose. A future version could preserve the current elementary/middle/high school interpretation while adding configurable target profiles, such as children’s literature, general public information, academic text, technical documentation, or literary fiction.

---

## Q11. Can machine learning help in readability and text quality assessment?

Yes, machine learning can help, especially when the goal is to combine many features into a predictive model. Petersen and Ostendorf use support vector machines to combine n-gram language models, parse features, and traditional reading-level measures [R3]. Aluísio et al. use machine learning approaches such as classification, regression, and ranking for readability assessment inside a text simplification context [R6].

However, machine learning requires training data, labels, evaluation metrics, and careful validation. For a small educational project, it may be better to start with interpretable rule-based and feature-based analysis, then later consider machine learning if suitable Italian datasets are available.

A practical direction is to design the system so that it can support both:

- interpretable metrics, such as Gulpease and sentence length;
- extensible feature extraction, which could later feed a machine-learning model.

---

## Q12. Why should explanations be included with the metrics?

Metrics are not useful if users do not understand them. A non-technical user may not know what “syntactic complexity” or “lexical diversity” means, and may not know how to improve a text based on a number.

Commercial tools such as Microsoft Editor and LanguageTool do not only return abstract scores. They present feedback as categories, warnings, and suggestions. Microsoft Editor includes spelling, grammar, clarity, conciseness, formality, vocabulary suggestions, and readability statistics in some contexts [R7]. LanguageTool provides grammar, spelling, punctuation, style suggestions, and paraphrasing support [R8].

For our project, every metric should have:

- a short explanation;
- the reason why it matters;
- an interpretation of the result;
- examples of problematic text segments;
- possible improvement suggestions.

This would make the analyzer more useful as an editorial support tool.

---

## Q13. What is the relationship between readability assessment and text simplification?

Readability assessment can identify difficult parts of a text, while text simplification attempts to make them easier to understand. The two tasks are closely related.

READ-IT was developed with a view to text simplification for Italian texts [R5]. Aluísio et al. also embed readability assessment into a text simplification authoring system, where the tool helps users understand the impact of simplification choices [R6].

For our project, full automatic simplification may be too ambitious at the beginning. A more realistic goal is to provide readability warnings and suggestions, leaving the final rewriting decision to the user.

Possible future features include:

- suggesting sentence splitting;
- identifying sentences with many subordinate clauses;
- detecting rare or difficult words;
- suggesting simpler alternatives.

---

## Q14. Why should the system avoid replacing human judgment?

Text quality includes subjective aspects such as style, creativity, voice, emotional effect, and narrative intention. These cannot be fully captured by automatic metrics.

A sentence may be long because it is badly written, but it may also be long for stylistic reasons. A repeated word may be accidental, or it may be intentionally used for emphasis. A low readability score may indicate a problem for general audiences, but not necessarily for a literary audience.

Therefore, the analyzer should be positioned as a decision-support tool. It can help authors and editors notice potential issues, but it should not claim to determine whether a text is good or bad.

---

## Q15. What can existing editorial tools teach us?

Existing editorial tools show that users benefit from categorized, actionable feedback rather than raw statistics only.

Microsoft Editor separates basic spelling and grammar from advanced refinements such as clarity, conciseness, formality, and vocabulary suggestions [R7]. LanguageTool offers grammar, spelling, punctuation, style checking, and paraphrasing support, and its core functionality can be self-hosted or integrated as an API [R8].

These tools suggest that a text quality analyzer should organize findings into categories such as:

- readability;
- grammar and spelling;
- vocabulary;
- repetition;
- syntax;
- cohesion;
- style;
- report summary.

They also show the importance of usability: users should see what the issue is, where it occurs, and why it matters.

---

## Q16. What should be the role of Italian NLP tools?

Italian NLP tools can provide the linguistic annotations needed for deeper analysis. Tokenization, sentence segmentation, lemmatization, part-of-speech tagging, dependency parsing, and named entity recognition are useful for readability and text quality metrics.

spaCy provides linguistic annotations such as tokens, lemmas, POS tags, dependency labels, sentence segmentation, and named entities [R9]. Tint is an Italian NLP pipeline based on Stanford CoreNLP and supports tokenization, sentence splitting, morphological analysis, lemmatization, POS tagging, dependency parsing, named entity recognition, and other components [R10].

For our project, spaCy is a practical default because the existing prototype already uses it. Tint can be considered as a reference or future alternative, especially if more Italian-specific NLP components are needed.

---

# 2. Existing SE-25 Text Quality Evaluator: Analysis

## 2.1 Overview of the existing prototype

The existing SE-25 Text Quality Evaluator is a Python desktop application that analyzes Italian `.docx` files. The repository README describes it as a tool that extracts lexical information from `.docx` files and helps users understand where a text is weaker in terms of grammatical structure or lexicon by calculating numerical indexes [R11].

The README lists the following metrics:

- **Gulpease Index (GIX)**: an Italian readability index;
- **Syntactic Complexity Index (SCIX)**: a measure of sentence-structure complexity;
- **Lexical Diversity Index (LDIX)**: a measure of vocabulary variety;
- **Base Vocabulary check**: a word-level indication of whether a word belongs to the Italian base vocabulary.

The inspected source code and prototype behavior also show the use of:

- `python-docx` for reading Word documents;
- `spaCy` with the Italian model `it_core_news_sm`;
- `langdetect` for warning users when a non-Italian document is detected;
- `PyQt5` for the graphical interface;
- local base vocabulary files loaded from the `VdB` directory;
- paragraph-level Gulpease analysis;
- readability interpretation for elementary school, middle school, and high school levels [R12].

The current prototype should therefore be described as an Italian readability and vocabulary analysis tool with paragraph-level feedback, not as a full grammar checker or a complete editorial assistant.

---

## 2.2 Current behavior summary

The prototype currently analyzes the following aspects:

| Area | Current behavior |
|---|---|
| File input | The system loads `.docx` files. |
| Language check | The system warns the user when the uploaded document is probably not Italian. |
| Paragraph-level readability | Each non-empty paragraph receives a Gulpease score. |
| Global readability | The whole document receives a global Gulpease score. |
| Educational-level interpretation | Gulpease scores are interpreted for elementary school, middle school, and high school levels. |
| Basic statistics | The system counts words, unique words, sentences, and letters. |
| Lexical diversity | The system calculates a lexical diversity index. |
| Syntactic complexity | The system calculates a syntactic complexity index based on sentence, clause, and t-unit information. |
| Base vocabulary | The system classifies words according to Italian base vocabulary categories. |
| Visual highlighting | Vocabulary categories are visually highlighted in the text. |

The prototype does not currently appear to provide the following functions:

| Area | Current limitation |
|---|---|
| Grammar correction | The system does not provide grammar corrections. |
| Spelling correction | The system does not suggest spelling corrections. |
| Repetition detection | The system does not explicitly detect repeated words, lemmas, or expressions. |
| Style suggestions | The system does not provide clarity, conciseness, tone, or formality suggestions. |
| Text coherence | The system does not evaluate discourse coherence or logical flow. |
| Narrative quality | The system does not analyze plot, pacing, dialogue balance, or character distribution. |
| Semantic quality | The system does not check whether the content is meaningful or consistent. |
| Report export | The system does not clearly provide an exportable analysis report. |
| Configurable thresholds | The user cannot configure thresholds for readability, repetitions, or sentence length. |
| Custom target audience | The system uses fixed elementary/middle/high school interpretations, but the user cannot define a custom target audience or text genre. |

---

## 2.3 What the prototype currently does well

### 1. It is already Italian-oriented

The use of Gulpease and Italian base vocabulary makes the prototype relevant for Italian texts. This is a strong point because Italian-specific analysis is necessary for this project.

### 2. It warns users when the document is not Italian

The prototype performs a language check and warns users when the uploaded document is probably not Italian. This is important because Italian-specific metrics may be invalid or misleading on texts written in other languages.

This should be described as a warning mechanism, not as multilingual support. The tool remains Italian-focused.

### 3. It provides more than one metric

The prototype does not rely only on a single score. It already includes readability, syntactic complexity, lexical diversity, and vocabulary information. This is aligned with the research view that text quality requires multiple indicators.

### 4. It provides paragraph-level readability analysis

The prototype calculates Gulpease not only globally, but also paragraph by paragraph. This is a strong feature because it helps users locate which parts of the document are easier or harder to read.

This is also aligned with research on local readability assessment and text simplification [R5], [R6].

### 5. It interprets readability for educational levels

The prototype compares readability against elementary school, middle school, and high school levels. This is important because readability depends on the intended reader.

This should be considered a basic form of audience-aware readability interpretation. The limitation is not that the prototype ignores audience completely, but that the audience model is fixed to three educational levels.

### 6. It uses NLP instead of only raw counts

The code uses spaCy to process text, split it into sentences, and inspect syntactic dependencies. This creates a basis for more advanced analysis later.

### 7. It works locally

Because the prototype is a desktop application, texts can be processed locally. This is useful from a privacy perspective, especially when users analyze unpublished manuscripts or editorial material.

### 8. It has a simple starting workflow

The current usage is straightforward: the user opens a `.docx` file and receives statistics, paragraph-level scores, and vocabulary highlighting. This is appropriate for a first prototype.

---

## 2.4 Current limitations of the prototype

### 1. Input support is narrow

The current workflow is focused on `.docx` files. This is useful, but an editorial tool may also need plain text input, pasted text, Markdown, or PDF support.

### 2. Paragraph-level analysis exists, but sentence-level analysis is missing

The prototype already provides paragraph-level Gulpease analysis. Therefore, the limitation is not the absence of local feedback. The limitation is that the tool does not clearly identify which sentences inside a paragraph are responsible for low readability.

Research such as READ-IT emphasizes the value of sentence-level readability assessment [R5]. A future version could preserve paragraph-level analysis and add sentence-level feedback.

### 3. The educational-level interpretation is fixed

The tool already interprets readability for elementary school, middle school, and high school levels. This is useful, but the user cannot define a custom target audience or select a specific genre.

For example, the system does not currently allow the user to choose:

- children’s literature;
- school textbook;
- general public article;
- academic text;
- technical documentation;
- literary fiction;
- professional editorial revision.

Therefore, the limitation is not the absence of target audience awareness. The limitation is that the current audience interpretation is fixed to three educational levels.

### 4. The metrics need clearer explanations

The current README lists formulas and short descriptions, but users may still need clearer explanations and examples. A user should understand what each metric means and how to act on it.

This is especially important for syntactic complexity and lexical diversity, which may be less intuitive than Gulpease.

### 5. Vocabulary highlighting may be misunderstood as error detection

The prototype visually highlights vocabulary categories. This is useful, but users may misunderstand highlighted words as spelling or grammar errors.

A word outside the base vocabulary is not necessarily wrong. It may be technical, literary, specialized, or simply less frequent. The interface and documentation should clearly explain the meaning of these highlights.

### 6. Very short text units may produce misleading readability scores

Very short headings or fragments can receive very high Gulpease scores. This can be misleading because readability formulas are less reliable on extremely short text units.

The system should distinguish body paragraphs from headings or mark very short fragments as unreliable for readability interpretation.

### 7. Lexical diversity is too simple if used alone

The current lexical diversity calculation is based on unique words divided by total words. This is easy to understand, but it is sensitive to text length and may not be enough for robust lexical analysis.

Lexical diversity should be interpreted together with repetition, vocabulary difficulty, syntactic complexity, and readability.

### 8. Syntactic complexity needs validation and safer handling

The prototype computes syntactic complexity using sentence, clause, and t-unit information. This is a promising direction, but it should be documented and tested carefully. Edge cases such as very short texts, zero clauses, or parsing errors should be handled explicitly.

### 9. There is no clear report-generation layer

The current tool displays statistics, paragraph-level scores, and highlights in the interface, but the repository does not clearly describe exportable reports. For an editorial workflow, a report would be useful for saving or comparing analyses.


# 3. Research-Based Improvement Direction for the Existing Prototype

The following improvement directions are not final requirements. They are research-based ideas that can later be transformed into formal requirements.

## 3.1 Improve the conceptual model of “text quality”

The current prototype focuses on readability, syntactic complexity, lexical diversity, and base vocabulary. These are good starting points, but research suggests that quality should also consider discourse, cohesion, and audience [R1], [R2].

Possible future categories:

- readability;
- lexical richness;
- vocabulary difficulty;
- syntactic complexity;
- repetitions;
- cohesion and discourse;
- grammar and spelling;
- narrative/editorial structure.

This would move the tool from a small metric calculator toward a broader editorial assistant.

---

## 3.2 Extend local feedback from paragraphs to sentences

The prototype already provides paragraph-level readability through Gulpease scores. The next improvement should be to make local feedback more precise.

Possible outputs:

- “This sentence is long compared to the document average.”
- “This paragraph has a lower readability score than the rest of the text.”
- “This sentence contains multiple subordinate clauses.”
- “This section contains many rare or non-basic vocabulary items.”
- “This paragraph is difficult mainly because of long sentences.”
- “This paragraph is difficult mainly because of vocabulary complexity.”

This would make the tool more actionable while preserving the existing paragraph-level analysis.

---

## 3.3 Make metrics explainable

Each metric should be accompanied by a clear explanation. This is important because authors and editors may not be familiar with mathematical formulas.

For example in the current prototype:

- **Gulpease**: explains general readability for Italian.
- **Educational-level interpretation**: explains whether the text is easy or difficult for elementary, middle, or high school readers.
- **Lexical diversity**: estimates vocabulary variety, but can be affected by text length.
- **Syntactic complexity**: estimates how complex sentence structures are.
- **Base vocabulary**: indicates whether words belong to common Italian vocabulary lists.

But the system should also explain limitations. For example, a high lexical diversity score is not always better, non-base vocabulary is not necessarily incorrect, and syntactic complexity is not always a defect in literary writing.

---

## 3.4 Extend audience modeling beyond fixed school levels

The existing elementary/middle/high school interpretation is useful and should be preserved. However, future versions could extend it by allowing the user to choose or define a target profile.

Possible target profiles:

- elementary school readers;
- middle school readers;
- high school readers;
- general public;
- academic readers;
- technical readers;
- children’s literature;
- literary fiction.

This would allow the analyzer to evaluate the same text differently depending on its intended audience and purpose.

---

## 3.5 Strengthen Italian NLP processing

The current prototype already uses spaCy, which supports tokenization, POS tagging, lemmatization, dependency parsing, sentence segmentation, and named entities [R9]. This can be used more systematically.

Potential NLP-based extensions:

- lemma-based repetition detection;
- POS distribution analysis;
- dependency-based complexity metrics;
- named entity distribution for characters and places;
- paragraph-level sentence statistics;
- recognition of discourse connectives;
- detection of passive constructions or subordinate clauses.

Tint could be used as a comparison point because it is specifically designed for Italian NLP and supports a broad set of Italian processing modules [R10].

---

## 3.6 Add repetition and lexical pattern analysis

Repetition is important in editorial quality analysis. Some repetition is intentional, but excessive repetition may indicate weak style.

Possible repetition analyses:

- repeated words;
- repeated lemmas;
- repeated bigrams and trigrams;
- repeated sentence openings;
- overused adjectives or adverbs;
- repeated character names in nearby sentences.

This should be configurable because literary texts may intentionally use repetition. The tool should report repeated patterns as warnings, not as automatic errors.

---

## 3.7 Add cohesion and discourse indicators

Research on text quality shows that discourse and cohesion matter [R1], [R2]. Full discourse parsing may be too complex for an initial implementation, but simple indicators could still be useful.

Possible cohesion indicators:

- entity continuity between adjacent sentences;
- abrupt disappearance of main entities;
- repeated references to characters;
- sentence-to-sentence lexical overlap;
- use of discourse connectives;
- paragraph transition markers.

For narrative texts, named entity recognition could help approximate character distribution and presence across chapters or paragraphs.

---

## 3.8 Add optional grammar and style checking

The current prototype is not primarily a grammar checker. However, grammar and spelling are part of perceived text quality.

A future version could keep grammar checking separate from readability analysis:

- readability metrics;
- lexical metrics;
- syntax metrics;
- grammar/spelling suggestions;
- style suggestions.

This separation would make the system easier to understand and maintain.

---

## 3.9 Add reliability handling for short text units

Since the prototype calculates paragraph-level Gulpease scores, it should handle very short paragraphs carefully.

Possible solutions:

- skip readability calculation for very short paragraphs;
- label short fragments as “not enough text for reliable readability analysis”;
- separate headings from body paragraphs;
- calculate readability only for paragraphs above a minimum word threshold.

This would prevent headings or small fragments from being interpreted as highly readable complete paragraphs.

---

## 3.10 Add report generation

A useful editorial tool should allow users to export the results. A report could include:

- global scores;
- paragraph-level Gulpease scores;
- elementary/middle/high school readability interpretation;
- sentence-level warnings;
- repeated words and expressions;
- vocabulary analysis;
- explanations of each metric;
- possible improvement suggestions.

The report could be exported as Markdown, PDF, DOCX, or HTML. Markdown may be a good first step because it is simple and easy to version-control.

---

# 4. Resource Descriptions

## R1. Revisiting Readability: A Unified Framework for Predicting Text Quality

This paper is highly relevant because it treats readability as a broader text quality problem. It combines lexical, syntactic, and discourse features and shows that discourse relations are strongly associated with perceived text quality.

Usefulness for this project:

- supports the idea that text quality should not be reduced to one formula;
- motivates discourse and cohesion indicators;
- motivates combining multiple feature types;
- helps justify why readability, vocabulary, syntax, and discourse should be separate categories.

---

## R2. Coh-Metrix

Coh-Metrix is a computational tool for analyzing text cohesion, language, and readability through many measures. It is useful as an example of a multi-level text analysis system.

Usefulness for this project:

- motivates moving beyond surface readability formulas;
- supports cohesion and discourse indicators;
- provides a model for organizing many metrics into a broader analysis framework.

---

## R3. A Machine Learning Approach to Reading Level Assessment

This paper is relevant because it uses machine learning to combine n-gram language models, parse features, and traditional reading-level measures. It also discusses the limits of traditional formulas and the variability of human reading-level annotation.

Usefulness for this project:

- supports combining different features;
- shows why machine learning can improve reading-level assessment;
- highlights the need to consider target readers;
- warns that human judgment may vary.

---

## R4. Gulpease Index

The Gulpease Index is a formula designed for Italian readability. It is directly relevant because the existing prototype already uses it.

Usefulness for this project:

- provides an Italian-specific readability baseline;
- is easy to explain and compute;
- can be used as a global document-level readability indicator;
- supports educational-level interpretation;
- should be complemented with other metrics.

---

## R5. READ-IT

READ-IT is one of the most important references for this project because it is an advanced readability assessment tool for Italian. It combines raw text, lexical, morpho-syntactic, and syntactic information and supports document-level and sentence-level readability assessment.

Usefulness for this project:

- supports Italian-specific NLP analysis;
- motivates sentence-level feedback;
- motivates lexical, morpho-syntactic, and syntactic features;
- connects readability assessment with text simplification.

---

## R6. Readability Assessment for Text Simplification

This paper is useful because it connects readability assessment with authoring and simplification tools. It shows how readability feedback can help users understand the effect of simplification choices.

Usefulness for this project:

- supports actionable feedback rather than only scores;
- motivates sentence-level warnings;
- motivates integration between analysis and editorial revision;
- supports using features from lexical, syntactic, semantic, and discursive levels.

---

## R7. Microsoft Editor

Microsoft Editor is a practical reference for how a writing assistant presents feedback to users. It includes spelling, grammar, clarity, conciseness, formality, vocabulary suggestions, and readability statistics in some contexts.

Usefulness for this project:

- helps define user-facing feedback categories;
- shows how metrics and suggestions can be presented in a writing workflow;
- motivates separating basic checks from advanced style refinements.

---

## R8. LanguageTool

LanguageTool is a grammar, spelling, punctuation, and style checking tool. Its core functionality is open source and can be self-hosted or used through an API.

Usefulness for this project:

- possible future grammar/spelling component;
- useful comparison for feedback cards and suggestions;
- supports the idea of separating grammar checking from readability analysis.

---

## R9. spaCy

spaCy is an NLP library that supports tokenization, POS tagging, lemmatization, dependency parsing, sentence segmentation, and named entity recognition.

Usefulness for this project:

- already used by the existing prototype;
- supports Italian NLP processing through Italian models;
- can be used for sentence-level and syntax-level metrics;
- can support named entity analysis for narrative texts.

---

## R10. Tint

Tint is an Italian NLP pipeline based on Stanford CoreNLP. It provides tokenization, sentence splitting, morphological analysis, lemmatization, POS tagging, dependency parsing, named entity recognition, and other tools.

Usefulness for this project:

- useful as an Italian-specific NLP reference;
- possible future alternative or comparison to spaCy;
- supports the need for language-aware processing.

---

## R11 - R12. SE-25 Text Quality Evaluator repository

The existing SE-25 repository is the starting prototype for the project. It currently provides `.docx`-based text analysis and calculates several indexes such as Gulpease, syntactic complexity, lexical diversity, and base vocabulary information.

Usefulness for this project:

- provides the baseline implementation;
- must be reverse-engineered and documented;
- helps identify current strengths and limitations;
- can be extended using the research directions described above.

---

# 5. Reference List

[R1] Pitler, E., & Nenkova, A. (2008). *Revisiting Readability: A Unified Framework for Predicting Text Quality*. EMNLP 2008.  
https://aclanthology.org/D08-1020/

[R2] Graesser, A. C., McNamara, D. S., Louwerse, M. M., & Cai, Z. (2004). *Coh-Metrix: Analysis of text on cohesion and language*.  
https://www.researchgate.net/publication/8358727_Coh-Metrix_Analysis_of_text_on_cohesion_and_language

[R3] Petersen, S. E., & Ostendorf, M. (2009). *A machine learning approach to reading level assessment*. Computer Speech & Language.  
https://people.cs.pitt.edu/~litman/courses/slate/pdf/csl09.pdf

[R4] Lucisano, P., & Piemontese, M. E. (1988). *GULPEASE: Una formula per la predizione della difficoltà dei testi in lingua italiana*.  
https://iris.uniroma1.it/handle/11573/450554

[R5] Dell’Orletta, F., Montemagni, S., & Venturi, G. (2011). *READ–IT: Assessing Readability of Italian Texts with a View to Text Simplification*. SLPAT 2011.  
https://aclanthology.org/W11-2308/  
Additional READ-IT documentation:  
http://www.italianlp.it/wp-content/uploads/2016/01/Documentazione-READ-IT.pdf

[R6] Aluísio, S., Specia, L., Gasperin, C., & Scarton, C. (2010). *Readability Assessment for Text Simplification*. NAACL HLT Workshop on Innovative Use of NLP for Building Educational Applications.  
https://aclanthology.org/W10-1001/

[R7] Microsoft Support. *Microsoft Editor checks grammar and more in documents, mail, and the web*.  
https://support.microsoft.com/en-us/word/microsoft-editor-checks-grammar-and-more-in-documents-mail-and-the-web

[R8] LanguageTool. *Grammar checker and open-source development documentation*.  
https://languagetool.org/  
https://languagetool.org/dev

[R9] spaCy Documentation. *Linguistic Features*.  
https://spacy.io/usage/linguistic-features

[R10] Tint — The Italian NLP Tool.  
https://tint.fbk.eu/  
https://github.com/dhfbk/tint

[R11] SE-25 Text Quality Evaluator repository.  
https://github.com/mnarizzano/se-25-textquality/tree/dev

[R12] SE-25 Text Quality Evaluator source files.  
https://github.com/mnarizzano/se-25-textquality/tree/dev/src/main