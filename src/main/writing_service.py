import copy
import re

import spacy

from pages.corrector import GrammarCorrector
from pages.evaluator import GrammarEvaluator
from pages.repetition_analyzer import RepetitionAnalyzer
from pages.text_redundancy_checker import (
    analyze_text,
    apply_pleonasm_replacements,
    split_sentences,
    warmup_pleonasm_cache,
)
from pages.text_rewriter import TextRewriter


# ---------------------------------------------------------------------------
# Shared thresholds
# ---------------------------------------------------------------------------

USER_CHOICE_THRESHOLD = 0.85
MERGE_THRESHOLD = 0.65
FAST_WORD_THRESHOLD = 0.92
SLOW_WORD_THRESHOLD = 0.88
FAST_SENT_THRESHOLD = 0.82
SLOW_SENT_THRESHOLD = 0.82


class WritingService:
    """
    Orchestrates the complete Italian text-quality workflow.

    The service keeps the API architecture simple:
    1. Analyze selected text.
    2. Return every reviewable finding with stable decision ids.
    3. Apply the user's decisions.
    4. Send the selected analysis context to the LLM for rewriting.
    """

    def __init__(self):
        self.nlp_model = spacy.load("it_core_news_lg")
        warmup_pleonasm_cache(self.nlp_model)

        self.corrector = GrammarCorrector()
        self.evaluator = GrammarEvaluator()
        self.repetition_analyzer = RepetitionAnalyzer(nlp=self.nlp_model)
        self.rewriter = TextRewriter(
            model="llama3.1",
            nlp=self.nlp_model,
            user_choice_threshold=USER_CHOICE_THRESHOLD,
            merge_threshold=MERGE_THRESHOLD,
        )

    # -----------------------------------------------------------------------
    # Generic helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """Collapse whitespace so sentence matching survives minor spacing changes."""
        return re.sub(r"\s+", " ", (text or "").strip())

    @staticmethod
    def _has_prefixed_decision(decisions: dict, prefix: str) -> bool:
        return any(str(key).startswith(prefix) for key in decisions)

    @staticmethod
    def _with_ids(items: list[dict], prefix: str) -> list[dict]:
        """Return shallow copies with stable ids such as grammar:1."""
        result = []
        for index, item in enumerate(items, start=1):
            clone = dict(item)
            clone.setdefault("id", f"{prefix}:{index}")
            result.append(clone)
        return result

    @staticmethod
    def _first_suggestion(match: dict) -> str:
        suggestions = match.get("suggestions") or []
        if not suggestions:
            return ""
        suggestion = str(suggestions[0]).strip()
        return suggestion.split("/")[0].strip()

    def _safe_replace(self, text: str, old: str, new: str) -> str:
        """
        Replace a sentence-like chunk while tolerating whitespace differences.
        Used for user decisions that remove one redundant sentence.
        """
        needle = self._normalize(old)
        pattern = re.escape(needle)
        pattern = re.sub(r"\\ ", r"\\s+", pattern)
        replaced = re.sub(pattern, new, self._normalize(text), count=1, flags=re.IGNORECASE)
        replaced = re.sub(r"\s+([.,!?;:])", r"\1", replaced)
        return self._normalize(replaced)

    @staticmethod
    def _replace_word_once(text: str, old_word: str, new_word: str) -> str:
        """Replace the first whole-word occurrence of old_word."""
        if not old_word or not new_word or old_word == new_word:
            return text

        pattern = r"\b" + re.escape(old_word) + r"\b"
        return re.sub(pattern, new_word, text, count=1, flags=re.IGNORECASE)

    @staticmethod
    def _contains_text(text: str, needle: str) -> bool:
        """Case-insensitive text containment that tolerates repeated spaces."""
        if not needle:
            return False

        pattern = re.escape(re.sub(r"\s+", " ", needle.strip()))
        pattern = re.sub(r"\\ ", r"\\s+", pattern)
        return bool(re.search(pattern, re.sub(r"\s+", " ", text or ""), flags=re.IGNORECASE))

    def _segment_protected_texts(self, text: str, protected_texts: list[str]) -> list[dict]:
        """
        Split text into rewrite/protected segments.

        Protected segments are never sent to Ollama. This is the hard guarantee
        that user choices such as "Not accept" cannot be overwritten by the LLM.
        """
        working = self._normalize(text)
        matches = []

        for protected in protected_texts:
            protected = self._normalize(protected)
            if not protected:
                continue

            pattern = re.escape(protected)
            pattern = re.sub(r"\\ ", r"\\s+", pattern)
            match = re.search(pattern, working, flags=re.IGNORECASE)
            if match:
                matches.append((match.start(), match.end(), working[match.start():match.end()]))

        if not matches:
            return [{"type": "rewrite", "text": working}]

        matches.sort(key=lambda item: item[0])
        non_overlapping = []
        last_end = -1
        for start, end, value in matches:
            if start < last_end:
                continue
            non_overlapping.append((start, end, value))
            last_end = end

        segments = []
        cursor = 0
        for start, end, value in non_overlapping:
            before = working[cursor:start].strip()
            if before:
                segments.append({"type": "rewrite", "text": before})
            segments.append({"type": "protected", "text": value})
            cursor = end

        after = working[cursor:].strip()
        if after:
            segments.append({"type": "rewrite", "text": after})

        return segments

    def _apply_protected_texts_to_segments(
        self,
        segments: list[dict],
        protected_texts: list[str],
    ) -> list[dict]:
        """Add phrase-level protected spans inside existing rewrite segments."""
        if not protected_texts:
            return segments

        result = []
        for segment in segments:
            if segment["type"] == "protected":
                result.append(segment)
                continue
            result.extend(self._segment_protected_texts(segment["text"], protected_texts))
        return result

    # -----------------------------------------------------------------------
    # Analysis
    # -----------------------------------------------------------------------

    def _sentence_index(self, sentences: list[str], sentence: str, used: set[int]) -> int | None:
        """Find the first unused sentence index matching the given text."""
        target = self._normalize(sentence).lower()
        for index, candidate in enumerate(sentences):
            if index in used:
                continue
            if self._normalize(candidate).lower() == target:
                used.add(index)
                return index
        return None

    def _classify_redundant_pairs(
        self,
        pairs: list[tuple],
        source_text: str,
    ) -> tuple[list[dict], list[dict]]:
        """Split sentence pairs into manual user-choice and merge-candidate lists."""
        user_choice_candidates = []
        merge_candidates = []
        source_sentences = split_sentences(source_text)

        for index, pair in enumerate(pairs, start=1):
            sent_a = pair[0]
            sent_b = pair[1]
            score = pair[2]
            category = pair[3] if len(pair) > 3 else ""
            used_indices: set[int] = set()

            payload = {
                "sentence_1": sent_a,
                "sentence_2": sent_b,
                "sentence_1_index": self._sentence_index(source_sentences, sent_a, used_indices),
                "sentence_2_index": self._sentence_index(source_sentences, sent_b, used_indices),
                "similarity": score,
                "category": category,
            }

            if score >= USER_CHOICE_THRESHOLD:
                user_choice_candidates.append({**payload, "id": str(index)})
            elif score >= MERGE_THRESHOLD:
                merge_candidates.append({**payload, "id": f"merge:{index}"})

        return user_choice_candidates, merge_candidates

    def _group_synonym_repetitions(self, synonym_pairs: list[dict]) -> list[dict]:
        """
        Group synonym pairs by connected components inside the same sentence.

        Example:
        cortese-gentile, cortese-garbato, gentile-garbato -> one card
        vecchio-anziano and bello-attraente in the same sentence -> two cards
        because the graphs are disconnected.
        """
        groups: list[dict] = []

        by_sentence: dict[str, list[tuple[str, str]]] = {}
        for item in synonym_pairs:
            pair = list(item.get("pair", []))
            if len(pair) != 2:
                continue
            sentence = item.get("sentence", "")
            by_sentence.setdefault(sentence, []).append((pair[0], pair[1]))

        for sentence, pairs in by_sentence.items():
            adjacency: dict[str, set[str]] = {}
            for first, second in pairs:
                adjacency.setdefault(first, set()).add(second)
                adjacency.setdefault(second, set()).add(first)

            seen: set[str] = set()
            for word in adjacency:
                if word in seen:
                    continue

                stack = [word]
                component: list[str] = []
                seen.add(word)

                while stack:
                    current = stack.pop()
                    component.append(current)
                    for neighbour in adjacency[current]:
                        if neighbour not in seen:
                            seen.add(neighbour)
                            stack.append(neighbour)

                component_pairs = [
                    [first, second]
                    for first, second in pairs
                    if first in component and second in component
                ]
                groups.append(
                    {
                        "id": f"synonym:{len(groups) + 1}",
                        "words": sorted(component),
                        "pairs": component_pairs,
                        "sentence": sentence,
                    }
                )

        return groups

    def _build_review_options(
        self,
        grammar_matches: list[dict],
        repetition_analysis: dict,
        redundancy_report: dict,
        user_choice_candidates: list[dict],
        merge_candidates: list[dict],
    ) -> dict:
        """Create one UI-friendly list for every reviewable analysis section."""
        synonym_repetitions = self._group_synonym_repetitions(
            repetition_analysis.get("synonym_repetition") or []
        )

        similar_words = []
        for index, item in enumerate(redundancy_report.get("similar_words") or [], start=1):
            similar_words.append(
                {
                    "id": f"similar:{index}",
                    "word_1": item[0],
                    "word_2": item[1],
                    "similarity": item[2],
                }
            )

        return {
            "grammar": grammar_matches,
            "pleonasms": redundancy_report.get("pleonasms") or [],
            "synonym_repetitions": synonym_repetitions,
            "similar_words": similar_words,
            "redundant_sentences": user_choice_candidates,
            "merge_candidates": merge_candidates,
        }

    def analyze_only(self, text: str, fast: bool = True) -> dict:
        """Run analysis without performing the final LLM rewrite."""
        word_threshold = FAST_WORD_THRESHOLD if fast else SLOW_WORD_THRESHOLD
        sent_threshold = FAST_SENT_THRESHOLD if fast else SLOW_SENT_THRESHOLD

        grammar_result = self.corrector.correct_text(text)

        original_text = grammar_result["original"]
        grammar_text = grammar_result["corrected"]
        polished_text = grammar_result["polished"]
        grammar_matches = self._with_ids(grammar_result["matches"], "grammar")

        grammar_metrics_before_rewrite = self.evaluator.evaluate(
            original_text,
            grammar_text,
        )

        repetition_corrected = self.repetition_analyzer.analyze(grammar_text)

        redundancy_report = analyze_text(
            grammar_text,
            word_sim_threshold=word_threshold,
            sent_sim_threshold=sent_threshold,
            nlp=self.nlp_model,
            max_similar_tokens=80 if fast else 140,
        )
        redundancy_report = copy.deepcopy(redundancy_report)
        redundancy_report["pleonasms"] = self._with_ids(
            redundancy_report.get("pleonasms", []),
            "pleonasm",
        )

        pleonasm_cleaned_text = apply_pleonasm_replacements(
            grammar_text,
            redundancy_report["pleonasms"],
        )

        repetition_for_rewrite = (
            self.repetition_analyzer.analyze(pleonasm_cleaned_text)
            if pleonasm_cleaned_text != grammar_text
            else repetition_corrected
        )

        user_choice_candidates, merge_candidates = self._classify_redundant_pairs(
            redundancy_report.get("redundant_sentences", []),
            grammar_text,
        )

        review_options = self._build_review_options(
            grammar_matches=grammar_matches,
            repetition_analysis=repetition_for_rewrite,
            redundancy_report=redundancy_report,
            user_choice_candidates=user_choice_candidates,
            merge_candidates=merge_candidates,
        )

        return {
            "original": original_text,
            "grammar_corrected": grammar_text,
            "polished": polished_text,
            "pleonasm_cleaned": pleonasm_cleaned_text,
            "grammar_matches": grammar_matches,
            "grammar_metrics_before_rewrite": grammar_metrics_before_rewrite,
            "repetition_analysis": repetition_for_rewrite,
            "redundancy_report": redundancy_report,
            "user_choice_candidates": user_choice_candidates,
            "merge_candidates": merge_candidates,
            "review_options": review_options,
        }

    # -----------------------------------------------------------------------
    # User decisions
    # -----------------------------------------------------------------------

    def _apply_grammar_decisions(self, analysis: dict, decisions: dict) -> str:
        """
        Apply only the grammar corrections accepted by the user.

        If the caller sends no grammar decisions, the old behaviour is kept:
        LanguageTool's fully corrected text is used as the rewrite base.
        When review decisions exist, only explicitly accepted suggestions are
        applied; ignored or unselected cards leave the original span unchanged.
        """
        if not self._has_prefixed_decision(decisions, "grammar:"):
            return analysis["grammar_corrected"]

        text = analysis["original"]
        matches = sorted(
            analysis.get("grammar_matches", []),
            key=lambda item: int(item.get("offset", 0)),
            reverse=True,
        )

        for match in matches:
            decision = decisions.get(match["id"], "apply")
            if decision in {"keep", "ignore"}:
                continue

            suggestion = self._first_suggestion(match)
            if not suggestion:
                continue

            start = int(match.get("offset", 0))
            end = start + int(match.get("length", 0))
            text = text[:start] + suggestion + text[end:]

        return self._normalize(text)

    def _selected_pleonasms(self, analysis: dict, decisions: dict) -> list[dict]:
        pleonasms = analysis["redundancy_report"].get("pleonasms", [])
        if not self._has_prefixed_decision(decisions, "pleonasm:"):
            return pleonasms
        return [
            item for item in pleonasms
            if decisions.get(item["id"], "replace") not in {"keep", "ignore"}
        ]

    def _synonym_groups(self, analysis: dict) -> list[dict]:
        """Return grouped synonym cards, rebuilding them for legacy analysis payloads."""
        groups = (
            analysis.get("review_options", {})
            .get("synonym_repetitions", [])
        )
        if groups:
            return groups
        return self._group_synonym_repetitions(
            analysis.get("repetition_analysis", {}).get("synonym_repetition") or []
        )

    def _collapse_synonym_sequence(
        self,
        text: str,
        group: dict,
        chosen_word: str,
    ) -> str:
        """
        Collapse one synonym list in its sentence to a single chosen word.

        This avoids turning "cortese, gentile e garbato" into
        "cortese, cortese e cortese". The user's selected word remains once;
        the alternative synonyms in that local list are removed.
        """
        words = [
            self._normalize(str(word))
            for word in group.get("words") or []
            if self._normalize(str(word))
        ]
        words = sorted(set(words), key=len, reverse=True)
        chosen_word = self._normalize(chosen_word)

        if len(words) < 2 or chosen_word.lower() not in {word.lower() for word in words}:
            return text

        result = self._normalize(text)
        sentence = self._normalize(group.get("sentence", ""))
        search_start = 0
        search_end = len(result)

        if sentence:
            sentence_pattern = re.escape(sentence)
            sentence_pattern = re.sub(r"\\ ", r"\\s+", sentence_pattern)
            sentence_match = re.search(sentence_pattern, result, flags=re.IGNORECASE)
            if sentence_match:
                search_start = sentence_match.start()
                search_end = sentence_match.end()

        target = result[search_start:search_end]
        word_pattern = r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b"
        separator = r"(?:\s*(?:,|;|/)\s*|\s+\b(?:e|ed|o|oppure)\b\s+|\s+)"
        sequence_pattern = word_pattern + r"(?:" + separator + word_pattern + r")+"

        collapsed = re.sub(
            sequence_pattern,
            chosen_word,
            target,
            count=1,
            flags=re.IGNORECASE,
        )

        if collapsed != target:
            updated = result[:search_start] + collapsed + result[search_end:]
            return self._normalize(updated)

        # Fallback for less regular wording: replace the first non-chosen
        # synonym with the chosen word, then leave the rest for the rewrite.
        for word in words:
            if word != chosen_word:
                replaced = self._replace_word_once(target, word, chosen_word)
                if replaced != target:
                    updated = result[:search_start] + replaced + result[search_end:]
                    return self._normalize(updated)

        return result

    def _apply_synonym_decisions(self, text: str, analysis: dict, decisions: dict) -> str:
        """
        Apply explicit synonym choices.

        keep_word:<word> collapses the local synonym sequence to one chosen
        word. Other values leave the text unchanged for direct preview.
        """
        result = text
        synonym_groups = self._synonym_groups(analysis)

        for group in synonym_groups:
            decision = decisions.get(group["id"], "reduce")
            words = list(group.get("words") or [])
            if len(words) < 2:
                continue

            if decision.startswith("keep_word:"):
                chosen = decision.split(":", 1)[1]
                result = self._collapse_synonym_sequence(result, group, chosen)
            elif decision == "keep_word_1":
                result = self._collapse_synonym_sequence(result, group, words[0])
            elif decision == "keep_word_2" and len(words) > 1:
                result = self._collapse_synonym_sequence(result, group, words[1])

        return self._normalize(result)

    def _filter_repetition_analysis(self, repetition_analysis: dict, decisions: dict) -> dict:
        """Remove synonym findings the user explicitly ignored."""
        filtered = copy.deepcopy(repetition_analysis)

        groups = self._group_synonym_repetitions(filtered.get("synonym_repetition") or [])
        allowed_pairs: set[tuple[str, str, str]] = set()
        for group in groups:
            decision = decisions.get(group["id"], "reduce")
            if decision != "reduce":
                continue
            for first, second in group.get("pairs", []):
                allowed_pairs.add((group.get("sentence", ""), first, second))

        synonyms = []
        for item in filtered.get("synonym_repetition") or []:
            pair = list(item.get("pair", []))
            if len(pair) != 2:
                continue
            key = (item.get("sentence", ""), pair[0], pair[1])
            if key in allowed_pairs:
                synonyms.append(item)
        filtered["synonym_repetition"] = synonyms
        filtered["has_synonym_repetition"] = bool(synonyms)

        return filtered

    def _filter_redundancy_report(self, redundancy_report: dict, decisions: dict) -> dict:
        """Remove similar-word and merge findings the user explicitly ignored."""
        filtered = copy.deepcopy(redundancy_report)

        filtered["pleonasms"] = [
            item for item in filtered.get("pleonasms", [])
            if decisions.get(item.get("id", ""), "replace") not in {"keep", "ignore"}
        ]

        similar_words = []
        for index, item in enumerate(filtered.get("similar_words") or [], start=1):
            if decisions.get(f"similar:{index}", "reduce") not in {"ignore", "keep"}:
                similar_words.append(item)
        filtered["similar_words"] = similar_words

        redundant_sentences = []
        for index, pair in enumerate(filtered.get("redundant_sentences") or [], start=1):
            decision = decisions.get(str(index), decisions.get(f"merge:{index}", "merge"))
            if decision in {"ignore", "keep_1", "keep_2", "keep_both"}:
                continue
            redundant_sentences.append(pair)
        filtered["redundant_sentences"] = redundant_sentences

        return filtered

    def _build_decision_summary(self, analysis: dict, decisions: dict) -> dict:
        """Summarise selected and ignored items for the LLM prompt."""
        summary = {
            "grammar": [],
            "pleonasms": [],
            "repeated_words": [],
            "synonym_repetitions": [],
            "similar_words": [],
            "redundant_sentences": [],
            "merge_candidates": [],
        }

        for match in analysis.get("grammar_matches", []):
            decision = decisions.get(match["id"], "apply")
            summary["grammar"].append(
                {
                    "label": match.get("wrong_text", ""),
                    "decision": decision,
                    "suggestion": self._first_suggestion(match),
                    "note": match.get("message", ""),
                }
            )

        for item in analysis["redundancy_report"].get("pleonasms", []):
            decision = decisions.get(item["id"], "replace")
            summary["pleonasms"].append(
                {
                    "phrase": item.get("phrase", ""),
                    "decision": decision,
                    "suggestion": item.get("replacement", ""),
                    "note": item.get("explanation", ""),
                }
            )

        for word, count in (analysis["repetition_analysis"].get("repeated_words") or {}).items():
            summary["repeated_words"].append(
                {
                    "word": word,
                    "decision": "auto_reduce",
                    "note": f"{count} occurrences",
                }
            )

        for item in self._synonym_groups(analysis):
            words = item.get("words", [])
            summary["synonym_repetitions"].append(
                {
                    "label": " / ".join(words),
                    "decision": decisions.get(item["id"], "reduce"),
                    "note": item.get("sentence", ""),
                }
            )

        for index, item in enumerate(
            analysis["redundancy_report"].get("similar_words") or [],
            start=1,
        ):
            summary["similar_words"].append(
                {
                    "label": f"{item[0]} / {item[1]}",
                    "decision": decisions.get(f"similar:{index}", "reduce"),
                    "note": f"similarity {item[2]}",
                }
            )

        for item in analysis.get("user_choice_candidates", []):
            summary["redundant_sentences"].append(
                {
                    "label": f"{item['sentence_1']} | {item['sentence_2']}",
                    "decision": decisions.get(item["id"], "keep_both"),
                    "note": f"similarity {item['similarity']}",
                }
            )

        for item in analysis.get("merge_candidates", []):
            summary["merge_candidates"].append(
                {
                    "label": f"{item['sentence_1']} | {item['sentence_2']}",
                    "decision": decisions.get(item["id"], "merge"),
                    "note": f"similarity {item['similarity']}",
                }
            )

        return summary

    def _protected_texts_for_decisions(self, analysis: dict, decisions: dict) -> list[str]:
        """
        Collect text spans that must not be changed by Ollama.

        Prompt instructions are helpful, but this list is the actual guardrail:
        protected text is split out before the LLM call and stitched back after.
        """
        protected: list[str] = []

        for match in analysis.get("grammar_matches", []):
            if decisions.get(match["id"], "apply") in {"keep", "ignore"}:
                protected.append(match.get("wrong_text", ""))

        for item in analysis.get("redundancy_report", {}).get("pleonasms", []):
            if decisions.get(item["id"], "replace") in {"keep", "ignore"}:
                protected.append(item.get("phrase", ""))

        for group in self._synonym_groups(analysis):
            decision = decisions.get(group["id"], "reduce")
            words = list(group.get("words") or [])
            if decision == "ignore":
                protected.append(group.get("sentence", ""))
            elif decision.startswith("keep_word:"):
                chosen = decision.split(":", 1)[1]
                protected.append(
                    self._collapse_synonym_sequence(group.get("sentence", ""), group, chosen)
                )
                protected.append(chosen)
            elif decision == "keep_word_1" and words:
                protected.append(
                    self._collapse_synonym_sequence(group.get("sentence", ""), group, words[0])
                )
                protected.append(words[0])
            elif decision == "keep_word_2" and len(words) > 1:
                protected.append(
                    self._collapse_synonym_sequence(group.get("sentence", ""), group, words[1])
                )
                protected.append(words[1])

        for index, item in enumerate(
            analysis.get("redundancy_report", {}).get("similar_words") or [],
            start=1,
        ):
            if decisions.get(f"similar:{index}", "reduce") in {"ignore", "keep"}:
                protected.extend([str(item[0]), str(item[1])])

        for item in analysis.get("user_choice_candidates", []):
            decision = decisions.get(item["id"], "keep_both")
            if decision == "keep_both":
                protected.extend([item.get("sentence_1", ""), item.get("sentence_2", "")])

        for item in analysis.get("merge_candidates", []):
            decision = decisions.get(item["id"], "merge")
            if decision == "ignore":
                protected.extend([item.get("sentence_1", ""), item.get("sentence_2", "")])

        # Keep order, drop empty duplicates.
        unique = []
        seen = set()
        for text in protected:
            normalised = self._normalize(text)
            if not normalised or normalised.lower() in seen:
                continue
            seen.add(normalised.lower())
            unique.append(normalised)
        return unique

    def _sentence_at_index(self, text: str, index: int | None) -> str:
        """Return the current sentence at index, or an empty string if invalid."""
        if index is None:
            return ""

        sentences = split_sentences(text)
        index = int(index)
        if 0 <= index < len(sentences):
            return self._normalize(sentences[index])
        return ""

    def _remove_sentence_candidate(
        self,
        text: str,
        sentence: str,
        index: int | None,
    ) -> str:
        """
        Remove a rejected sentence from the current text.

        Text matching is safer when accepted grammar/pleonasm choices changed
        sentence indexes. The stored index is only a fallback for cases where
        the sentence text was normalized differently by the analyzer.
        """
        working = self._normalize(text)
        sentence = self._normalize(sentence)

        if sentence and self._contains_text(working, sentence):
            return self._safe_replace(working, sentence, "")

        if index is None:
            return working

        sentences = split_sentences(working)
        index = int(index)
        if 0 <= index < len(sentences):
            return self._normalize(
                " ".join(
                    current
                    for current_index, current in enumerate(sentences)
                    if current_index != index
                )
            )
        return working

    def apply_sentence_decisions(
        self,
        text: str,
        candidates: list[dict],
        decisions: dict,
    ) -> tuple[list[dict], str]:
        """
        Remove only the sentence alternatives the user explicitly rejected.

        Kept sentences are protected from the LLM; rewrite segments are still
        improved normally.
        """
        working = self._normalize(text)
        to_protect: list[str] = []

        for candidate in candidates:
            decision = decisions.get(candidate["id"], "keep_both")
            if decision == "keep_both":
                to_protect.extend([
                    self._sentence_at_index(working, candidate.get("sentence_1_index"))
                    or self._normalize(candidate["sentence_1"]),
                    self._sentence_at_index(working, candidate.get("sentence_2_index"))
                    or self._normalize(candidate["sentence_2"]),
                ])
                continue

            if decision == "ignore":
                to_protect.extend([
                    self._normalize(candidate["sentence_1"]),
                    self._normalize(candidate["sentence_2"]),
                ])
                continue

            if decision not in {"keep_1", "keep_2"}:
                continue

            s1 = self._normalize(candidate["sentence_1"])
            s2 = self._normalize(candidate["sentence_2"])
            index_1 = candidate.get("sentence_1_index")
            index_2 = candidate.get("sentence_2_index")

            if decision == "keep_1":
                to_protect.append(self._sentence_at_index(working, index_1) or s1)
                working = self._remove_sentence_candidate(working, s2, index_2)
            else:
                to_protect.append(self._sentence_at_index(working, index_2) or s2)
                working = self._remove_sentence_candidate(working, s1, index_1)
        working = re.sub(r"\s{2,}", " ", working).strip()

        if not to_protect:
            return [{"type": "rewrite", "text": working}], working

        return self._segment_protected_texts(working, to_protect), working

    def _enforce_sentence_decisions(
        self,
        text: str,
        candidates: list[dict],
        decisions: dict,
    ) -> str:
        """
        Re-apply sentence keep/remove decisions after the LLM returns.

        Protected segments prevent most accidental changes. This final pass is
        a second guardrail for user choices such as Keep B: if the model drops
        the kept sentence or brings back the rejected sentence, the user's
        decision wins.
        """
        result = self._normalize(text)

        for candidate in candidates:
            fallback = "merge" if str(candidate.get("id", "")).startswith("merge:") else "keep_both"
            decision = decisions.get(candidate["id"], fallback)
            sentence_1 = self._normalize(candidate.get("sentence_1", ""))
            sentence_2 = self._normalize(candidate.get("sentence_2", ""))

            if decision == "keep_1":
                result = self._remove_sentence_candidate(result, sentence_2, None)
            elif decision == "keep_2":
                result = self._remove_sentence_candidate(result, sentence_1, None)

        return self._normalize(result)

    def _rewrite_segments(
        self,
        segments: list[dict],
        repetition_analysis: dict,
        redundancy_report: dict,
        mode: str,
        decision_summary: dict,
    ) -> str:
        """Rewrite only editable segments, then stitch protected text back in."""
        result_parts: list[str] = []

        for segment in segments:
            if segment["type"] == "protected":
                result_parts.append(segment["text"])
                continue

            chunk = segment["text"].strip()
            if not chunk:
                continue

            rewritten = self.rewriter.rewrite(
                text=chunk,
                repetition_analysis=repetition_analysis,
                redundancy_report=redundancy_report,
                mode=mode,
                decision_summary=decision_summary,
            )
            result_parts.append(rewritten.strip())

        return re.sub(r"\s{2,}", " ", " ".join(result_parts)).strip()

    def _build_direct_preview_text(self, analysis: dict, decisions: dict) -> str:
        """
        Build the deterministic result available immediately after analysis.

        This never calls Ollama. It applies accepted grammar replacements,
        accepted pleonasm replacements, explicit synonym word choices, and
        sentence keep/remove decisions.
        """
        grammar_selected_text = self._apply_grammar_decisions(analysis, decisions)
        selected_pleonasms = self._selected_pleonasms(analysis, decisions)
        preview_text = apply_pleonasm_replacements(grammar_selected_text, selected_pleonasms)
        preview_text = self._apply_synonym_decisions(preview_text, analysis, decisions)

        sentence_candidates = (
            analysis.get("user_choice_candidates", [])
            + analysis.get("merge_candidates", [])
        )
        _, preview_text = self.apply_sentence_decisions(
            preview_text,
            sentence_candidates,
            decisions,
        )

        return self._normalize(preview_text)

    def preview_after_analysis(
        self,
        text: str,
        decisions: dict | None = None,
        analysis: dict | None = None,
    ) -> dict:
        """Return the current analysis-only preview without calling Ollama."""
        decisions = decisions or {}
        analysis = analysis or self.analyze_only(text, fast=True)
        final_text = self._build_direct_preview_text(analysis, decisions)

        return {
            "final": final_text,
            "decision_summary": self._build_decision_summary(analysis, decisions),
        }

    # -----------------------------------------------------------------------
    # Rewrite
    # -----------------------------------------------------------------------

    def rewrite_after_analysis(
        self,
        text: str,
        mode: str = "concise",
        decisions: dict | None = None,
        final_check: bool = False,
        analysis: dict | None = None,
    ) -> dict:
        decisions = decisions or {}
        analysis = analysis or self.analyze_only(text, fast=True)

        # Step 1: apply all user decisions deterministically
        rewrite_base = self._build_direct_preview_text(analysis, decisions)

        # Step 2: fresh analysis on the already-cleaned text
        fresh_analysis = self.analyze_only(rewrite_base, fast=True)

        # Step 3: send to Ollama with fresh analysis, no decision context
        rewritten_text = self.rewriter.rewrite(
            text=rewrite_base,
            repetition_analysis=fresh_analysis["repetition_analysis"],
            redundancy_report=fresh_analysis["redundancy_report"],
            mode=mode,
            decision_summary=None,  # no decisions — Ollama just rewrites
        )

        if final_check:
            final_result = self.corrector.correct_text(rewritten_text)
            final_text = final_result["corrected"]
            final_matches = final_result["matches"]
        else:
            final_text = rewritten_text
            final_matches = []

        final_metrics = self.evaluator.evaluate(analysis["original"], final_text)

        return {
            "rewritten": rewritten_text,
            "final": final_text,
            "final_grammar_matches": final_matches,
            "final_metrics": final_metrics,
            "decision_summary": self._build_decision_summary(analysis, decisions),
        }

    # -----------------------------------------------------------------------
    # Full pipeline
    # -----------------------------------------------------------------------

    def process(
        self,
        text: str,
        mode: str = "concise",
        final_check: bool = False,
        fast: bool = True,
        include_full_analysis: bool = False,
    ) -> dict:
        analysis = self.analyze_only(text, fast=fast)
        rewrite_result = self.rewrite_after_analysis(
            text=text,
            mode=mode,
            decisions={},
            final_check=final_check,
            analysis=analysis,
        )
        return {**analysis, **rewrite_result}
