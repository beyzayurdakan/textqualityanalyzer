import language_tool_python

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

_MASCULINE_NOUNS: set[str] = {
    # -ma words (Greek neuter)
    "problema", "programma", "sistema", "tema", "clima", "schema",
    "panorama", "diploma", "dramma", "poema", "aroma", "fantasma",
    "prisma", "teorema", "dilemma", "dogma", "enigma", "emblema",
    "trauma", "plasma", "telegramma", "diagramma", "anagramma",
    "epigramma", "ideogramma", "monogramma", "ologramma", "diorama",
    "reuma", "edema", "eczema", "enema", "enfisema", "glaucoma",
    "melanoma", "carcinoma", "adenoma", "sarcoma", "linfoma",
    # -ta words
    "atleta", "pianeta", "poeta", "profeta", "cometa",
    "delta", "beta", "eta", "zeta", "theta",
    # -ista used as masculine
    "artista", "giornalista", "pianista", "violinista", "ciclista",
    "dentista", "terrorista", "comunista", "fascista", "capitalista",
    "socialista", "ottimista", "pessimista", "realista", "idealista",
    "protagonista", "antagonista",
    # other
    "brindisi", "alibi", "safari", "koala", "panda", "gorilla",
    "lama", "vaglia", "sosia",
}

_FEMININE_NOUNS: set[str] = {
    "mano", "radio", "foto", "moto", "auto", "metro", "bici", "eco",
    "dinamo", "libido",
    "nazione", "situazione", "soluzione", "relazione", "collaborazione",
    "comunicazione", "informazione", "istruzione", "tradizione", "funzione",
    "condizione", "azione", "reazione", "produzione", "distribuzione",
    "percezione", "eccezione", "connessione", "sessione", "missione",
    "passione", "discussione", "decisione", "conclusione", "dimensione",
    "attenzione", "intenzione", "menzione", "tensione", "pensione",
    "versione", "visione", "revisione", "previsione", "divisione",
    "invasione", "evasione", "persuasione", "illusione", "allusione",
    "città", "libertà", "verità", "qualità", "università", "attività",
    "capacità", "possibilità", "opportunità", "necessità", "realtà",
    "identità", "priorità", "difficoltà", "novità", "curiosità",
    "creatività", "nazionalità", "personalità",
    "crisi", "tesi", "analisi", "sintesi", "ipotesi", "diagnosi",
    "prognosi", "nevrosi", "psicosi", "metamorfosi", "osmosi",
    "parentesi", "enfasi", "perifrasi",
}

# Verbs that take ESSERE as auxiliary in compound tenses
_ESSERE_VERBS: set[str] = {
    "andare", "venire", "partire", "arrivare", "tornare", "uscire",
    "entrare", "salire", "scendere", "cadere", "fuggire", "scappare",
    "passare", "ritornare", "rientrare", "ripartire", "riuscire",
    "risalire", "rivenire", "nascere", "morire", "diventare", "divenire",
    "crescere", "invecchiare", "migliorare", "peggiorare", "guarire",
    "ammalarsi", "ingrassare", "dimagrire", "arrossire", "impallidire",
    "essere", "stare", "sembrare", "parere", "risultare", "apparire",
    "restare", "rimanere", "durare", "piacere", "dispiacere",
    "succedere", "accadere", "capitare", "mancare", "bastare",
    "costare", "servire", "importare", "interessare", "dipendere",
    "appartenere", "piovere", "nevicare", "grandinare", "tuonare",
    "comparire", "scomparire", "sparire", "emergere", "affiorare",
    "sorgere", "tramontare", "esistere", "vivere", "giacere",
    "cominciare", "iniziare", "finire", "terminare",
    "alzarsi", "lavarsi", "vestirsi", "sedersi", "fermarsi",
    "sentirsi", "trovarsi", "chiamarsi", "svegliarsi", "addormentarsi",
    "annoiarsi", "arrabbiarsi", "dimenticarsi", "innamorarsi",
    "perdersi", "riposarsi", "sbrigarsi", "sposarsi", "vergognarsi",
    "avvicinarsi", "accorgersi", "rendersi", "prepararsi",
}

# Verbs that can take EITHER essere OR avere depending on transitive use
# When used with a direct object → avere; otherwise → essere
_DUAL_AUXILIARY_VERBS: set[str] = {
    "aumentare", "cambiare", "cominciare", "crescere", "cuocere",
    "esplodere", "finire", "guarire", "salire", "fallire", "correre",
    "passare", "migliorare", "peggiorare", "iniziare", "terminare",
    "scendere", "montare", "volare", "bruciare", "affogare",
}

_PREP_ARTICLE_CONTRACTIONS = {
    ("di", "il"):  "del",
    ("di", "lo"):  "dello",
    ("di", "la"):  "della",
    ("di", "i"):   "dei",
    ("di", "gli"): "degli",
    ("di", "le"):  "delle",
    ("di", "l'"):  "dell'",
    ("a",  "il"):  "al",
    ("a",  "lo"):  "allo",
    ("a",  "la"):  "alla",
    ("a",  "i"):   "ai",
    ("a",  "gli"): "agli",
    ("a",  "le"):  "alle",
    ("a",  "l'"):  "all'",
    ("da", "il"):  "dal",
    ("da", "lo"):  "dallo",
    ("da", "la"):  "dalla",
    ("da", "i"):   "dai",
    ("da", "gli"): "dagli",
    ("da", "le"):  "dalle",
    ("da", "l'"):  "dall'",
    ("in", "il"):  "nel",
    ("in", "lo"):  "nello",
    ("in", "la"):  "nella",
    ("in", "i"):   "nei",
    ("in", "gli"): "negli",
    ("in", "le"):  "nelle",
    ("in", "l'"):  "nell'",
    ("su", "il"):  "sul",
    ("su", "lo"):  "sullo",
    ("su", "la"):  "sulla",
    ("su", "i"):   "sui",
    ("su", "gli"): "sugli",
    ("su", "le"):  "sulle",
    ("su", "l'"):  "sull'",
}

_CONTRACTED_TO_PARTS = {v: k for k, v in _PREP_ARTICLE_CONTRACTIONS.items()}

# Bare preposition each contracted form resolves to
_CONTRACTED_BARE_PREP = {
    contracted: prep
    for (prep, _art), contracted in _PREP_ARTICLE_CONTRACTIONS.items()
}

# Verb-preposition collocations.
# "wrong" lists only BARE prepositions (never contracted forms).
_VERB_PREP_RULES = {
    "andare": {
        "expected": "a",
        "wrong": ["in", "per", "su"],   # "al"/"allo" etc. are fine (a+article)
        "note": "'Andare' richiede 'a' (o forma contratta 'al/allo…') per moto a luogo.",
    },
    "venire": {
        "expected": "a",
        "wrong": ["in", "per"],
        "note": "'Venire' richiede 'a' per moto a luogo.",
    },
    "pensare": {
        "expected": "a",
        "wrong": ["su"],
        # "di" is valid with infinitive (pensare di fare), so we don't flag it
        "note": "'Pensare a qualcosa' (riflettere); 'pensare di fare' (avere intenzione).",
    },
    "ringraziare": {
        "expected": "per",
        "wrong": ["di"],
        "note": "'Ringraziare per qualcosa'.",
    },
    "dipendere": {
        "expected": "da",
        "wrong": ["di", "su"],
        "note": "'Dipendere da qualcosa/qualcuno'.",
    },
    "parlare": {
        "expected": "di",
        "wrong": ["su", "per"],
        "note": "'Parlare di qualcosa'.",
    },
    "accorgersi": {
        "expected": "di",
        "wrong": ["a", "su"],
        "note": "'Accorgersi di qualcosa'.",
    },
    "dimenticarsi": {
        "expected": "di",
        "wrong": ["a", "su"],
        "note": "'Dimenticarsi di qualcosa'.",
    },
    "preoccuparsi": {
        "expected": "di",
        "wrong": ["su", "per"],
        "note": "'Preoccuparsi di qualcosa'.",
    },
    "fidarsi": {
        "expected": "di",
        "wrong": ["a", "su", "in"],
        "note": "'Fidarsi di qualcuno'.",
    },
    "credere": {
        "expected": "a",
        "wrong": ["su", "per"],
        # "credere di" with infinitive is valid
        "note": "'Credere a qualcuno/qualcosa' (prestare fede).",
    },
}

_COPULAR_VERBS = {
    "essere", "sembrare", "parere", "diventare", "divenire", "restare",
    "rimanere", "apparire", "risultare", "sentirsi", "ritrovarsi",
    "rivelarsi", "dimostrarsi",
}

_REFLEXIVE_VERBS = {
    "lavarsi", "alzarsi", "sedersi", "vestirsi", "prepararsi",
    "fermarsi", "sentirsi", "trovarsi", "chiamarsi", "svegliarsi",
    "addormentarsi", "annoiarsi", "arrabbiarsi", "dimenticarsi",
    "innamorarsi", "perdersi", "riposarsi", "sbrigarsi", "sposarsi",
    "vergognarsi", "avvicinarsi", "accorgersi", "rendersi",
}

_REFLEXIVE_LEMMA_MAP = {
    "lavare": "lavarsi", "alzare": "alzarsi", "sedere": "sedersi",
    "vestire": "vestirsi", "preparare": "prepararsi", "fermare": "fermarsi",
    "sentire": "sentirsi", "trovare": "trovarsi", "chiamare": "chiamarsi",
    "svegliare": "svegliarsi", "addormentare": "addormentarsi",
    "annoiare": "annoiarsi", "arrabbiare": "arrabbiarsi",
    "dimenticare": "dimenticarsi", "innamorare": "innamorarsi",
    "perdere": "perdersi", "riposare": "riposarsi", "sbrigare": "sbrigarsi",
    "sposare": "sposarsi", "vergognare": "vergognarsi",
    "avvicinare": "avvicinarsi", "accorgere": "accorgersi",
    "rendere": "rendersi",
}

_NEGATIVE_POLARITY_WORDS = {
    "niente", "nulla", "nessuno", "nessuna", "mai", "nemmeno",
    "neanche", "neppure", "né", "affatto",
}

_WH_WORDS = {
    "cosa", "che", "chi", "come", "quando", "dove", "perché",
    "quanto", "quale", "quali",
}

_MODAL_VERBS = {
    "volere", "potere", "dovere", "sapere", "riuscire", "osare",
    "desiderare", "preferire", "sperare", "tentare", "cercare",
}

# Past participles of essere/stare that are NOT agreement targets
# (to avoid flagging "è stato" etc. as errors)
_ESSERE_STARE_PARTICIPLES = {"stato", "stata", "stati", "state"}


class GrammarCorrector:
    """
    Italian grammar checker combining LanguageTool and spaCy dependency rules.
    """

    def __init__(self, use_spacy: bool = True):
        self.tool = language_tool_python.LanguageTool("it")
        self.nlp = None
        if use_spacy and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("it_core_news_lg")
                self._build_dynamic_lexicons()
            except OSError:
                print("spaCy model not found. Run: python -m spacy download it_core_news_lg")

    # ------------------------------------------------------------------
    # Dynamic lexicon builder
    # ------------------------------------------------------------------

    def _build_dynamic_lexicons(self) -> None:
        _REFERENCE_CORPUS = """
        Il problema principale è la mancanza di risorse.
        Abbiamo sviluppato un nuovo programma informatico.
        Il sistema operativo si è aggiornato automaticamente.
        Il tema della conferenza era molto interessante.
        Il clima mediterraneo è molto piacevole.
        Hai seguito lo schema corretto per l'analisi.
        Il panorama dalla cima era mozzafiato.
        Ha ottenuto il diploma con il massimo dei voti.
        Il dramma si è svolto in tre atti.
        Ho letto un bellissimo poema epico.
        L'aroma del caffè si sentiva in tutto il corridoio.
        Il fantasma del castello spaventava i visitatori.
        Il teorema di Pitagora è fondamentale in geometria.
        Si trovava in un profondo dilemma morale.
        Il dogma religioso è stato messo in discussione.
        L'enigma è rimasto irrisolto per secoli.
        Il trauma psicologico ha richiesto un lungo recupero.
        Il plasma sanguigno è composto principalmente di acqua.
        Ha inviato un telegramma urgente al consolato.
        Il diagramma mostra l'andamento delle vendite.
        L'atleta professionista si allena ogni giorno.
        Il pianeta Marte è detto il pianeta rosso.
        Il poeta romantico ha scritto versi immortali.
        Il profeta aveva previsto la catastrofe.
        La mano destra è più forte della sinistra.
        La radio trasmetteva musica classica tutto il giorno.
        La foto del matrimonio era bellissima.
        La moto era parcheggiata sotto casa.
        La mia auto nuova è molto efficiente.
        La crisi economica ha colpito molte famiglie.
        La tesi di laurea è stata approvata con lode.
        L'analisi dei dati ha rivelato tendenze interessanti.
        La sintesi della ricerca è stata pubblicata ieri.
        L'ipotesi non è stata ancora verificata.
        La diagnosi è arrivata dopo una settimana di esami.
        La città di Roma è ricca di storia e cultura.
        La libertà di espressione è un diritto fondamentale.
        La verità è sempre più complessa di quanto appaia.
        La qualità del prodotto è migliorata notevolmente.
        L'università offre molti corsi di specializzazione.
        Mario è andato al supermercato stamattina.
        Siamo venuti apposta per salutarti.
        Il treno è partito in orario.
        Gli ospiti sono arrivati con molto anticipo.
        Mia sorella è tornata dalla Francia ieri sera.
        I bambini sono usciti a giocare nel parco.
        Il ladro è entrato dalla finestra posteriore.
        Luca è nato a Milano nel 1990.
        La nonna è morta serenamente nel sonno.
        L'acqua è caduta dal tavolo e ha bagnato tutto.
        Siamo saliti sul treno all'ultimo momento.
        Il gatto è sceso dall'albero con difficoltà.
        La situazione è diventata sempre più complicata.
        Il cielo è sembrato improvvisamente minaccioso.
        Il risultato è parso soddisfacente a tutti.
        Sono rimasto a casa tutto il giorno per via della pioggia.
        La bambina è restata sveglia fino a tardi.
        Il vaso è caduto dal davanzale e si è rotto.
        Abbiamo corso e siamo arrivati in tempo per lo spettacolo.
        L'estate è passata in fretta quest'anno.
        Il sole è tramontato dietro le montagne.
        Una nuova stella è comparsa nel cielo notturno.
        Il vecchio edificio è scomparso dopo la demolizione.
        Il sole è sorto all'alba colorando il cielo di rosso.
        La nebbia è emersa lentamente dalla valle.
        Alcuni dipendenti hanno espresso la loro opinione riguardo al progetto.
        Ieri sono andato al meeting aziendale e ho partecipato personalmente.
        """
        if self.nlp is None:
            return
        doc = self.nlp(_REFERENCE_CORPUS)
        for token in doc:
            lemma = token.lemma_.lower()
            text_lower = token.text.lower()
            gender = token.morph.get("Gender")
            pos = token.pos_
            if pos == "NOUN" and text_lower.endswith("a") and gender == ["Masc"] and lemma not in _MASCULINE_NOUNS:
                _MASCULINE_NOUNS.add(lemma)
            if pos == "NOUN" and (text_lower.endswith("o") or text_lower.endswith("e")) and gender == ["Fem"] and lemma not in _FEMININE_NOUNS:
                _FEMININE_NOUNS.add(lemma)
            if pos == "VERB" and lemma not in _ESSERE_VERBS:
                for child in token.children:
                    if child.dep_ == "aux" and child.lemma_.lower() == "essere":
                        _ESSERE_VERBS.add(lemma)
                        break

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------


    def _preserve_case(self, original: str, replacement: str) -> str:
        """Preserve simple capitalisation when building suggestions."""
        if not original or not replacement:
            return replacement
        if original.isupper():
            return replacement.upper()
        if original[0].isupper():
            return replacement.capitalize()
        return replacement

    def _replace_token_text(self, text: str, token, replacement: str) -> str:
        """Return the full sentence with one token replaced."""
        if not replacement:
            return ""
        return text[:token.idx] + replacement + text[token.idx + len(token.text):]

    def _remove_token_text(self, text: str, token) -> str:
        """Return the full sentence with one token removed and spaces cleaned."""
        start = token.idx
        end = token.idx + len(token.text)
        if end < len(text) and text[end:end + 1] == " ":
            end += 1
        elif start > 0 and text[start - 1:start] == " ":
            start -= 1
        return text[:start] + text[end:]

    def _suggest_article_for_noun(self, article, noun) -> str:
        """Suggest a simple definite/indefinite article matching noun gender/number."""
        lower = article.text.lower()
        gender = noun.morph.get("Gender")
        number = noun.morph.get("Number")
        g = gender[0] if gender else None
        n = number[0] if number else None

        # Override spaCy with project lexicons for common exception nouns.
        lemma = noun.lemma_.lower()
        if lemma in _MASCULINE_NOUNS:
            g = "Masc"
        elif lemma in _FEMININE_NOUNS:
            g = "Fem"

        if not g or not n:
            return ""

        indefinite = lower in {"un", "uno", "una", "un'"}
        if indefinite and n == "Sing":
            if g == "Fem":
                return self._preserve_case(article.text, "un'" if noun.text[:1].lower() in "aeiouàèéìòù" else "una")
            # Simple masculine default. Your project can later refine uno/un before z, s+consonant, etc.
            return self._preserve_case(article.text, "un")

        forms = {
            ("Masc", "Sing"): "il",
            ("Fem", "Sing"): "la",
            ("Masc", "Plur"): "i",
            ("Fem", "Plur"): "le",
        }
        suggestion = forms.get((g, n), "")
        return self._preserve_case(article.text, suggestion)

    def _suggest_finite_verb_number(self, verb, target_number: list) -> str:
        """Suggest a common finite verb form with the subject's number."""
        n = target_number[0] if target_number else None
        if not n:
            return ""
        lemma = verb.lemma_.lower()
        lower = verb.text.lower()
        maps = {
            "essere": {"Sing": "è", "Plur": "sono"},
            "avere": {"Sing": "ha", "Plur": "hanno"},
            "andare": {"Sing": "va", "Plur": "vanno"},
            "fare": {"Sing": "fa", "Plur": "fanno"},
            "stare": {"Sing": "sta", "Plur": "stanno"},
            "venire": {"Sing": "viene", "Plur": "vengono"},
            "potere": {"Sing": "può", "Plur": "possono"},
            "volere": {"Sing": "vuole", "Plur": "vogliono"},
            "dovere": {"Sing": "deve", "Plur": "devono"},
        }
        if lemma in maps:
            return self._preserve_case(verb.text, maps[lemma][n])

        # Limited regular fallback for present indicative 3rd person.
        if n == "Plur":
            if lower.endswith("a"):
                return self._preserve_case(verb.text, lower[:-1] + "ano")
            if lower.endswith("e"):
                return self._preserve_case(verb.text, lower[:-1] + "ono")
        if n == "Sing":
            if lower.endswith("ano"):
                return self._preserve_case(verb.text, lower[:-3] + "a")
            if lower.endswith("ono"):
                return self._preserve_case(verb.text, lower[:-3] + "e")
        return ""

    def _suggest_wrong_auxiliary_phrase(self, aux_token, participle_token, correct_aux_lemma: str) -> str:
        """Suggest a compact auxiliary + participle replacement phrase."""
        number = None
        gender = None
        for child in participle_token.children:
            if child.dep_ in ("nsubj", "nsubj:pass"):
                number = (child.morph.get("Number") or [None])[0]
                gender = (child.morph.get("Gender") or [None])[0]
                break
        number = number or (participle_token.morph.get("Number") or ["Sing"])[0]
        gender = gender or (participle_token.morph.get("Gender") or ["Masc"])[0]
        aux = "sono" if correct_aux_lemma == "essere" and number == "Plur" else "è" if correct_aux_lemma == "essere" else "hanno" if number == "Plur" else "ha"
        part = participle_token.text
        if correct_aux_lemma == "essere":
            part = self._inflect_italian(
                participle_token.text,
                participle_token.morph.get("Gender"),
                participle_token.morph.get("Number"),
                gender,
                number,
            ) or participle_token.text
        return f"{self._preserve_case(aux_token.text, aux)} {part}"

    def _suggest_subjunctive(self, verb) -> str:
        """Small high-frequency indicative → subjunctive suggestion map."""
        lower = verb.text.lower()
        forms = {
            "è": "sia", "sono": "siano", "sei": "sia", "siamo": "siamo", "siete": "siate",
            "ha": "abbia", "hanno": "abbiano", "hai": "abbia", "abbiamo": "abbiamo", "avete": "abbiate",
            "va": "vada", "vanno": "vadano", "fa": "faccia", "fanno": "facciano",
            "può": "possa", "possono": "possano", "deve": "debba", "devono": "debbano",
            "vuole": "voglia", "vogliono": "vogliano",
        }
        if lower in forms:
            return self._preserve_case(verb.text, forms[lower])
        if lower.endswith("a"):
            return self._preserve_case(verb.text, lower[:-1] + "i")
        if lower.endswith("e"):
            return self._preserve_case(verb.text, lower[:-1] + "a")
        if lower.endswith("ono"):
            return self._preserve_case(verb.text, lower[:-3] + "ino")
        return ""

    def _normalise_suggestions(self, suggestions: list | None, fallback: str = "") -> list:
        """Keep frontend output consistent: always return a clean suggestion list."""
        clean = []
        for suggestion in suggestions or []:
            if suggestion and suggestion not in clean:
                clean.append(suggestion)
        if not clean and fallback:
            clean.append(fallback)
        return clean[:5]

    def get_match_value(self, match, *names, default=None):
        for name in names:
            if hasattr(match, name):
                return getattr(match, name)
        return default

    def classify_lt_issue(self, category: str, rule: str) -> str:
        category = (category or "").upper()
        rule = (rule or "").upper()
        if category in ("PUNCTUATION", "TYPOGRAPHY", "CASING"):
            return "punctuation"
        if any(k in rule for k in ("COMMA", "APOSTROPHE", "WHITESPACE", "PUNCT")):
            return "punctuation"
        if category in ("TYPOS", "MISSPELLING"):
            return "spelling"
        return "grammar"

    def _issue(self, *, text: str, token, rule: str, message: str, suggestions: list = None) -> dict:
        return {
            "source": "spaCy",
            "issue_type": "grammar",
            "message": message,
            "rule": rule,
            "category": "GRAMMAR",
            "offset": token.idx,
            "length": len(token.text),
            "wrong_text": token.text,
            "context": text[max(0, token.idx - 30): token.idx + 40],
            "suggestions": self._normalise_suggestions(suggestions, fallback=token.text),
        }

    def _is_past_participle(self, token) -> bool:
        """Return True if the token is a past participle (VerbForm=Part, Tense=Past)."""
        return (
            "Part" in token.morph.get("VerbForm", [])
            and "Past" in token.morph.get("Tense", [])
        )

    def _is_finite_verb(self, token) -> bool:
        """Return True only for inflected finite verb forms (not participles, not infinitives)."""
        verb_form = token.morph.get("VerbForm", [])
        if not verb_form:
            # spaCy sometimes omits VerbForm for clear finite forms; allow AUX/VERB with mood/tense
            mood = token.morph.get("Mood", [])
            tense = token.morph.get("Tense", [])
            return bool(mood or tense)
        return "Fin" in verb_form or (
            "Part" not in verb_form
            and "Inf" not in verb_form
            and "Ger" not in verb_form
        )

    def _bare_prep(self, token_text: str) -> str:
        """
        Return the bare preposition for a token.
        If it is a contracted form (al, del, nel…), return the preposition part.
        Otherwise return the token text lowercased.
        """
        lower = token_text.lower()
        return _CONTRACTED_BARE_PREP.get(lower, lower)
    def _suggest_possessive(self, possessive: str, target_gender: list, target_number: list) -> str:
        """Return the correct form of a possessive determiner."""
        _POSSESSIVE_FORMS = {
            # (lemma_base, gender, number) → correct form
            ("mio",    "Masc", "Sing"): "mio",
            ("mio",    "Fem",  "Sing"): "mia",
            ("mio",    "Masc", "Plur"): "miei",
            ("mio",    "Fem",  "Plur"): "mie",
            ("tuo",    "Masc", "Sing"): "tuo",
            ("tuo",    "Fem",  "Sing"): "tua",
            ("tuo",    "Masc", "Plur"): "tuoi",
            ("tuo",    "Fem",  "Plur"): "tue",
            ("suo",    "Masc", "Sing"): "suo",
            ("suo",    "Fem",  "Sing"): "sua",
            ("suo",    "Masc", "Plur"): "suoi",
            ("suo",    "Fem",  "Plur"): "sue",
            ("nostro", "Masc", "Sing"): "nostro",
            ("nostro", "Fem",  "Sing"): "nostra",
            ("nostro", "Masc", "Plur"): "nostri",
            ("nostro", "Fem",  "Plur"): "nostre",
            ("vostro", "Masc", "Sing"): "vostro",
            ("vostro", "Fem",  "Sing"): "vostra",
            ("vostro", "Masc", "Plur"): "vostri",
            ("vostro", "Fem",  "Plur"): "vostre",
            ("loro",   "Masc", "Sing"): "loro",
            ("loro",   "Fem",  "Sing"): "loro",
            ("loro",   "Masc", "Plur"): "loro",
            ("loro",   "Fem",  "Plur"): "loro",
        }
        lower = possessive.lower()
        # Detect the lemma base from the surface form
        base = None
        if lower in ("mio", "mia", "miei", "mie"):
            base = "mio"
        elif lower in ("tuo", "tua", "tuoi", "tue"):
            base = "tuo"
        elif lower in ("suo", "sua", "suoi", "sue"):
            base = "suo"
        elif lower in ("nostro", "nostra", "nostri", "nostre"):
            base = "nostro"
        elif lower in ("vostro", "vostra", "vostri", "vostre"):
            base = "vostro"
        elif lower == "loro":
            return "loro"

        if base is None:
            return ""

        gender = target_gender[0] if target_gender else None
        number = target_number[0] if target_number else None
        if not gender or not number:
            return ""

        return _POSSESSIVE_FORMS.get((base, gender, number), "")


    def _suggest_agreement_form(self, token, target_gender: list, target_number: list) -> str:
        """
        Try to find the correct inflected form of a determiner or adjective
        by looking up all tokens in the doc that share the same lemma and
            match the target gender/number.
        """
        if self.nlp is None:
            return ""
        target_g = target_gender[0] if target_gender else None
        target_n = target_number[0] if target_number else None
        if not target_g or not target_n:
            return ""

        # Search the spaCy vocab for a form matching lemma + target morph
        lemma = token.lemma_.lower()
        # Re-parse a small probe to find the right form
        probe_map = {
            # (lemma, gender, number) → suggested surface form
            # Articles
            ("il",  "Masc", "Sing"): "il",
            ("il",  "Fem",  "Sing"): "la",
            ("il",  "Masc", "Plur"): "i",
            ("il",  "Fem",  "Plur"): "le",
            ("un",  "Masc", "Sing"): "un",
            ("un",  "Fem",  "Sing"): "una",
            # Common determiners
            ("questo", "Masc", "Sing"): "questo",
            ("questo", "Fem",  "Sing"): "questa",
            ("questo", "Masc", "Plur"): "questi",
            ("questo", "Fem",  "Plur"): "queste",
            ("quello", "Masc", "Sing"): "quello",
            ("quello", "Fem",  "Sing"): "quella",
            ("quello", "Masc", "Plur"): "quelli",
            ("quello", "Fem",  "Plur"): "quelle",
            ("bello",  "Masc", "Sing"): "bello",
            ("bello",  "Fem",  "Sing"): "bella",
            ("bello",  "Masc", "Plur"): "belli",
            ("bello",  "Fem",  "Plur"): "belle",
            ("buono",  "Masc", "Sing"): "buono",
            ("buono",  "Fem",  "Sing"): "buona",
            ("buono",  "Masc", "Plur"): "buoni",
            ("buono",  "Fem",  "Plur"): "buone",
            ("grande", "Masc", "Sing"): "grande",
            ("grande", "Fem",  "Sing"): "grande",
            ("grande", "Masc", "Plur"): "grandi",
            ("grande", "Fem",  "Plur"): "grandi",
        }
        result = probe_map.get((lemma, target_g, target_n))
        if result:
            return result

        # Generic Italian inflection fallback based on ending patterns
        return self._inflect_italian(token.text, token.morph.get("Gender"), token.morph.get("Number"), target_g, target_n)


    def _inflect_italian(self, word: str, src_gender: list, src_number: list, tgt_gender: str, tgt_number: str) -> str:
        """
        Simple rule-based Italian inflection for adjectives/determiners.
        Covers the most common -o/-a/-i/-e paradigm.
        """
        if not word or not tgt_gender or not tgt_number:
            return ""
        w = word.lower()

        # -o / -a / -i / -e paradigm (most Italian adjectives)
        endings = {
            ("Masc", "Sing"): "o",
            ("Fem",  "Sing"): "a",
            ("Masc", "Plur"): "i",
            ("Fem",  "Plur"): "e",
        }
        target_ending = endings.get((tgt_gender, tgt_number))
        if not target_ending:
            return ""

        # Strip current ending and attach target ending
        for ending in ("e", "i", "a", "o"):
            if w.endswith(ending):
                stem = w[:-1]
                result = stem + target_ending
                # Preserve original capitalisation
                if word[0].isupper():
                    result = result.capitalize()
                return result

        return ""

    def parse_language_tool_matches(self, text: str, matches: list) -> list:
        parsed = []
        for match in matches:
            offset = self.get_match_value(match, "offset", default=0)
            length = self.get_match_value(match, "errorLength", "error_length", default=0)
            category = self.get_match_value(match, "category", default="")
            rule = self.get_match_value(match, "ruleId", "rule_id", default="")
            parsed.append({
                "source": "LanguageTool",
                "issue_type": self.classify_lt_issue(category, rule),
                "message": self.get_match_value(match, "message", default=""),
                "rule": rule,
                "category": category,
                "offset": offset,
                "length": length,
                "wrong_text": text[offset: offset + length],
                "context": self.get_match_value(match, "context", default=""),
                "suggestions": self.get_match_value(match, "replacements", default=[])[:5],
            })
        return parsed

    # ------------------------------------------------------------------
    # Rule 1 – determiner / adjective ↔ noun agreement (pre-nominal)
    # ------------------------------------------------------------------

    def spacy_noun_agreement_issues(self, text: str) -> list:
        """
        Detect gender/number mismatches between a pre-nominal determiner or
        adjective and its governing noun.
        Skips possessives (handled by rule 3) and articles (handled by rule 5).
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if token.dep_ not in ("det", "amod"):
                continue
            # Skip articles and possessives — dedicated rules handle them
            if "Art" in token.morph.get("PronType", []):
                continue
            if token.dep_ == "det" and "Yes" in token.morph.get("Poss", []):
                continue
            head = token.head
            if head.pos_ not in ("NOUN", "PROPN"):
                continue
            # Only flag pre-nominal position
            if token.i >= head.i:
                continue
            t_gender = token.morph.get("Gender")
            t_number = token.morph.get("Number")
            h_gender = head.morph.get("Gender")
            h_number = head.morph.get("Number")
            mismatches = []
            if t_gender and h_gender and t_gender != h_gender:
                mismatches.append("genere")
            if t_number and h_number and t_number != h_number:
                mismatches.append("numero")
            if mismatches:
                suggestion = self._suggest_agreement_form(token, h_gender, h_number)
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_NOUN_AGREEMENT",
                    message=(
                        f"Accordo di {' e '.join(mismatches)}: "
                        f"'{token.text}' non concorda con '{head.text}'."
                    ),
                    suggestions=[suggestion] if suggestion else [],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 2 – subject–verb agreement (finite forms only)
    # ------------------------------------------------------------------

    def spacy_subject_verb_issues(self, text: str) -> list:
        """
        Detect number mismatches between a nominal subject and its FINITE verb.
        Past participles are explicitly excluded — they agree with the subject
        via rule 4, not here.
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        seen_pairs: set = set()

        for token in doc:
            if token.dep_ not in ("nsubj", "nsubj:pass"):
                continue
            subj = token
            head = token.head
            candidates = []

            if head.pos_ in ("VERB", "AUX"):
                candidates.append(head)
            if head.pos_ == "AUX":
                main_verb = head.head
                if main_verb.pos_ in ("VERB", "AUX"):
                    candidates.append(main_verb)
                for sibling in main_verb.children:
                    if sibling.dep_ == "aux" and sibling is not head:
                        candidates.append(sibling)

            for finite in candidates:
                # ✅ Skip past participles — not finite inflected forms
                if self._is_past_participle(finite):
                    continue
                # ✅ Skip infinitives and gerunds
                vf = finite.morph.get("VerbForm", [])
                if "Inf" in vf or "Ger" in vf:
                    continue

                pair_key = (subj.i, finite.i)
                if pair_key in seen_pairs:
                    continue

                s_number = subj.morph.get("Number")
                v_number = finite.morph.get("Number")

                if s_number and v_number and s_number != v_number:
                    seen_pairs.add(pair_key)
                    suggestion = self._suggest_finite_verb_number(finite, s_number)
                    issues.append(self._issue(
                        text=text, token=finite,
                        rule="SPACY_SUBJECT_VERB_AGREEMENT",
                        message=(
                            f"Accordo soggetto-verbo: "
                            f"'{subj.text}' è {s_number[0]}, "
                            f"ma '{finite.text}' è {v_number[0]}."
                        ),
                        suggestions=[suggestion] if suggestion else [],
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 3 – possessive ↔ noun agreement
    # ------------------------------------------------------------------

    def spacy_possessive_noun_issues(self, text: str) -> list:
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            is_possessive = (
                token.dep_ == "det:poss"
                or (token.pos_ == "DET" and "Yes" in token.morph.get("Poss", []))
            )
            if not is_possessive:
                continue
            head = token.head
            if head.pos_ not in ("NOUN", "PROPN"):
                continue
            t_gender = token.morph.get("Gender")
            t_number = token.morph.get("Number")
            h_gender = head.morph.get("Gender")
            h_number = head.morph.get("Number")
            mismatches = []
            if t_gender and h_gender and t_gender != h_gender:
                mismatches.append("genere")
            if t_number and h_number and t_number != h_number:
                mismatches.append("numero")
            if mismatches:
                suggestion = self._suggest_possessive(token.text, h_gender, h_number)
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_POSSESSIVE_NOUN_AGREEMENT",
                    message=(
                        f"Accordo possessivo-nome ({' e '.join(mismatches)}): "
                        f"'{token.text}' non concorda con '{head.text}'. "
                        f"(es. 'nostri progetto' → 'nostro progetto')"
                    ),
                    suggestions=[suggestion] if suggestion else [],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 4 – auxiliary ↔ past-participle agreement (essere only)
    # ------------------------------------------------------------------

    def spacy_aux_participle_issues(self, text: str) -> list:
        """
        When the auxiliary is essere, the past participle must agree with
        the subject in gender and number.
        Dual-auxiliary verbs (correre, passare…) are only flagged when
        the auxiliary actually is essere (not avere).
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)

        for token in doc:
            if not self._is_past_participle(token):
                continue
            # Skip "stato/stata/stati/state" — these are copula participles
            if token.lemma_.lower() in ("essere", "stare") or token.text.lower() in _ESSERE_STARE_PARTICIPLES:
                continue

            # Find an essere auxiliary in the same clause
            aux_essere = None
            for child in token.children:
                if child.dep_ == "aux" and child.lemma_.lower() in ("essere", "venire"):
                    aux_essere = child
                    break
            if aux_essere is None and token.head.lemma_.lower() in ("essere", "venire"):
                aux_essere = token.head
            if aux_essere is None:
                continue

            # For dual-auxiliary verbs, only flag when the aux IS essere
            # (if avere is also present, skip — transitivity makes avere correct)
            verb_lemma = token.lemma_.lower()
            if verb_lemma in _DUAL_AUXILIARY_VERBS:
                has_avere = any(
                    c.dep_ == "aux" and c.lemma_.lower() == "avere"
                    for c in token.children
                )
                if has_avere:
                    continue

            # Find the subject
            subject = None
            for child in token.children:
                if child.dep_ in ("nsubj", "nsubj:pass"):
                    subject = child
                    break
            if subject is None:
                for child in aux_essere.children:
                    if child.dep_ in ("nsubj", "nsubj:pass"):
                        subject = child
                        break
            if subject is None:
                continue

            s_gender = subject.morph.get("Gender")
            s_number = subject.morph.get("Number")
            p_gender = token.morph.get("Gender")
            p_number = token.morph.get("Number")

            mismatches = []
            if s_gender and p_gender and s_gender != p_gender:
                mismatches.append("genere")
            if s_number and p_number and s_number != p_number:
                mismatches.append("numero")

            if mismatches:
                suggestion = self._inflect_italian(token.text, token.morph.get("Gender"), token.morph.get("Number"), s_gender[0] if s_gender else None, s_number[0] if s_number else None)
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_AUX_PARTICIPLE_AGREEMENT",
                    message=(
                        f"Accordo ausiliare-participio ({' e '.join(mismatches)}): "
                        f"soggetto '{subject.text}' è "
                        f"{', '.join(s_gender + s_number)}, ma participio "
                        f"'{token.text}' è {', '.join(p_gender + p_number)}. "
                        f"(es. 'siamo tornato' → 'siamo tornati')"
                    ),
                    suggestions=[suggestion] if suggestion else [],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 5 – article ↔ noun agreement
    # ------------------------------------------------------------------

    def spacy_article_noun_issues(self, text: str) -> list:
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if not (token.pos_ == "DET" and "Art" in token.morph.get("PronType", [])):
                continue
            head = token.head
            if head.pos_ not in ("NOUN", "PROPN"):
                continue
            t_gender = token.morph.get("Gender")
            h_gender = head.morph.get("Gender")
            t_number = token.morph.get("Number")
            h_number = head.morph.get("Number")
            mismatches = []
            lemma = head.lemma_.lower()
            if lemma in _MASCULINE_NOUNS and t_gender == ["Fem"]:
                mismatches.append("genere (nome maschile con articolo femminile)")
            elif lemma in _FEMININE_NOUNS and t_gender == ["Masc"]:
                mismatches.append("genere (nome femminile con articolo maschile)")
            else:
                if t_gender and h_gender and t_gender != h_gender:
                    mismatches.append("genere")
                if t_number and h_number and t_number != h_number:
                    mismatches.append("numero")
            if mismatches:
                suggestion = self._suggest_article_for_noun(token, head) or self._suggest_agreement_form(token, h_gender, h_number)
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_ARTICLE_NOUN_AGREEMENT",
                    message=(
                        f"Accordo articolo-nome ({' e '.join(mismatches)}): "
                        f"'{token.text}' non concorda con '{head.text}'. "
                        f"(es. 'un ragazza' → 'una ragazza', 'la problema' → 'il problema')"
                    ),
                    suggestions=[suggestion] if suggestion else [],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 6 – post-nominal adjective agreement
    # ------------------------------------------------------------------

    def spacy_postnominal_adjective_issues(self, text: str) -> list:
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if not (token.dep_ == "amod" and token.head.pos_ in ("NOUN", "PROPN") and token.i > token.head.i):
                continue
            head = token.head
            t_gender = token.morph.get("Gender")
            t_number = token.morph.get("Number")
            h_gender = head.morph.get("Gender")
            h_number = head.morph.get("Number")
            mismatches = []
            if t_gender and h_gender and t_gender != h_gender:
                mismatches.append("genere")
            if t_number and h_number and t_number != h_number:
                mismatches.append("numero")
            if mismatches:
                suggestion = self._inflect_italian(token.text, token.morph.get("Gender"), token.morph.get("Number"), h_gender[0] if h_gender else None, h_number[0] if h_number else None)
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_POSTNOMINAL_ADJ_AGREEMENT",
                    message=(
                        f"Accordo aggettivo-nome ({' e '.join(mismatches)}): "
                        f"'{token.text}' non concorda con '{head.text}'. "
                        f"(es. 'case grande' → 'case grandi')"
                    ),
                    suggestions=[suggestion] if suggestion else [],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 7 – preposition contraction errors
    # ------------------------------------------------------------------

    def spacy_preposition_contraction_issues(self, text: str) -> list:
        """
        Flag bare PREP + ART sequences that should be written as a
        contracted articulated preposition.
        Only flags when the preposition and article are separate tokens
        and a known contracted form exists.
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        tokens = list(doc)
        for i, token in enumerate(tokens[:-1]):
            next_tok = tokens[i + 1]
            prep = token.text.lower()
            art = next_tok.text.lower()
            # Only flag if this is actually a preposition token
            if token.pos_ not in ("ADP",):
                continue
            contracted = _PREP_ARTICLE_CONTRACTIONS.get((prep, art))
            if contracted is None:
                continue
            # Skip if already immediately followed by the contracted form in text
            issues.append(self._issue(
                text=text, token=token,
                rule="SPACY_PREP_CONTRACTION",
                message=(
                    f"Preposizione articolata mancante: "
                    f"'{token.text} {next_tok.text}' → '{contracted}'."
                ),
                suggestions=[contracted],
            ))
        return issues

    # ------------------------------------------------------------------
    # Rule 8 – verb–preposition collocation
    # ------------------------------------------------------------------

    def spacy_verb_preposition_issues(self, text: str) -> list:
        """
        Detect verbs used with a wrong preposition.
        Contracted forms (al, del, nel…) are decomposed to their bare
        preposition before checking, so 'andato al meeting' is NOT flagged.
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if token.pos_ not in ("VERB", "AUX"):
                continue
            rule_entry = _VERB_PREP_RULES.get(token.lemma_.lower())
            if rule_entry is None:
                continue
            expected_prep = rule_entry["expected"]
            wrong_preps = rule_entry["wrong"]
            note = rule_entry.get("note", "")
            for child in token.children:
                if child.dep_ not in ("obl", "obl:agent", "nmod", "advmod"):
                    continue
                for grandchild in child.children:
                    if grandchild.dep_ == "case" and grandchild.pos_ == "ADP":
                        # ✅ Decompose contracted forms before checking
                        bare = self._bare_prep(grandchild.text)
                        if bare in wrong_preps:
                            issues.append(self._issue(
                                text=text, token=grandchild,
                                rule="SPACY_VERB_PREP_COLLOCATION",
                                message=(
                                    f"Preposizione errata dopo '{token.text}': "
                                    f"usato '{grandchild.text}', atteso '{expected_prep}'. {note}"
                                ),
                                suggestions=[expected_prep],
                            ))
        return issues

    # ------------------------------------------------------------------
    # Rule 9 – predicate adjective agreement
    # ------------------------------------------------------------------

    def spacy_predicate_adjective_issues(self, text: str) -> list:
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if token.pos_ != "ADJ":
                continue
            head = token.head
            subject = None
            is_predicate_adj = False

            # Pattern A: head is a copular verb
            if head.pos_ in ("VERB", "AUX") and head.lemma_.lower() in _COPULAR_VERBS:
                is_predicate_adj = True
                for child in head.children:
                    if child.dep_ in ("nsubj", "nsubj:pass"):
                        subject = child
                        break

            # Pattern B: ADJ is root with cop child
            if not is_predicate_adj:
                cop_child = None
                for child in token.children:
                    if child.dep_ == "cop" and child.lemma_.lower() in _COPULAR_VERBS:
                        cop_child = child
                        break
                if cop_child is not None:
                    is_predicate_adj = True
                    for child in token.children:
                        if child.dep_ in ("nsubj", "nsubj:pass"):
                            subject = child
                            break

            if not is_predicate_adj or subject is None:
                continue

            s_gender = subject.morph.get("Gender")
            s_number = subject.morph.get("Number")
            a_gender = token.morph.get("Gender")
            a_number = token.morph.get("Number")

            mismatches = []
            if s_gender and a_gender and s_gender != a_gender:
                mismatches.append("genere")
            if s_number and a_number and s_number != a_number:
                mismatches.append("numero")

            if mismatches:
                suggestion = self._inflect_italian(token.text, token.morph.get("Gender"), token.morph.get("Number"), s_gender[0] if s_gender else None, s_number[0] if s_number else None)
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_PREDICATE_ADJ_AGREEMENT",
                    message=(
                        f"Accordo aggettivo predicativo ({' e '.join(mismatches)}): "
                        f"soggetto '{subject.text}' è {', '.join(s_gender + s_number)}, "
                        f"ma '{token.text}' è {', '.join(a_gender + a_number)}. "
                        f"(es. 'Lei era simpatico' → 'Lei era simpatica')"
                    ),
                    suggestions=[suggestion] if suggestion else [],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 10 – clitic elision before vowel-initial verb
    # ------------------------------------------------------------------

    def spacy_clitic_agreement_issues(self, text: str) -> list:
        """
        Flag 'lo'/'la' that should be elided to 'l'' before a vowel-starting
        auxiliary or verb.
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        tokens = list(doc)
        for i, token in enumerate(tokens[:-1]):
            if token.text.lower() not in ("lo", "la"):
                continue
            next_tok = tokens[i + 1]
            if next_tok.pos_ not in ("VERB", "AUX"):
                continue
            next_lower = next_tok.text.lower()
            if next_lower and next_lower[0] in "aeiouàèéìòù":
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_CLITIC_ELISION",
                    message=(
                        f"Il clitico '{token.text}' deve essere eliso prima di "
                        f"'{next_tok.text}' (inizia per vocale): "
                        f"'{token.text} {next_tok.text}' → 'l'{next_tok.text}'."
                    ),
                    suggestions=[f"l'{next_tok.text}"],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 11 – partitive article misuse
    # ------------------------------------------------------------------

    def spacy_partitive_article_issues(self, text: str) -> list:
        _PARTITIVE_MORPH = {
            "del":   ("Masc", "Sing"),
            "dello": ("Masc", "Sing"),
            "della": ("Fem",  "Sing"),
            "dei":   ("Masc", "Plur"),
            "degli": ("Masc", "Plur"),
            "delle": ("Fem",  "Plur"),
        }
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if token.pos_ != "DET":
                continue
            lower = token.text.lower()
            if lower not in _PARTITIVE_MORPH:
                continue
            head = token.head
            if head.pos_ not in ("NOUN", "PROPN"):
                continue
            art_gender, art_number = _PARTITIVE_MORPH[lower]
            h_gender = head.morph.get("Gender")
            h_number = head.morph.get("Number")
            mismatches = []
            if h_gender and [art_gender] != h_gender:
                mismatches.append("genere")
            if h_number and [art_number] != h_number:
                mismatches.append("numero")
            if mismatches:
                target_gender = h_gender[0] if h_gender else "?"
                target_number = h_number[0] if h_number else "?"
                correct_map = {
                    ("Masc", "Sing"): "del/dello",
                    ("Fem",  "Sing"): "della",
                    ("Masc", "Plur"): "dei/degli",
                    ("Fem",  "Plur"): "delle",
                }
                suggestion = correct_map.get((target_gender, target_number), "?")
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_PARTITIVE_AGREEMENT",
                    message=(
                        f"Articolo partitivo errato ({' e '.join(mismatches)}): "
                        f"'{token.text}' non concorda con '{head.text}'. "
                        f"Usa '{suggestion}'. (es. 'del mele' → 'delle mele')"
                    ),
                    suggestions=[suggestion],
                ))
        return issues

    # ------------------------------------------------------------------
    # Rule 12 – missing reflexive clitic
    # ------------------------------------------------------------------

    def spacy_missing_reflexive_clitic(self, text: str) -> list:
        """
        Flag verbs that require a reflexive clitic but appear without one
        AND without a direct object (transitive use is fine).
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if token.pos_ not in ("VERB", "AUX"):
                continue
            reflexive_form = _REFLEXIVE_LEMMA_MAP.get(token.lemma_.lower())
            if reflexive_form is None:
                continue
            # Suppress if there is a direct object → transitive use
            has_obj = any(c.dep_ in ("obj", "iobj") for c in token.children)
            if has_obj:
                continue
            # Suppress if clitic present as child
            has_clitic = any(
                c.pos_ == "PRON" and "Yes" in c.morph.get("Clitic", [])
                for c in token.children
            )
            if has_clitic:
                continue
            # Suppress if clitic present in left window
            idx = token.i
            left_window = doc[max(0, idx - 2): idx]
            has_left_clitic = any(
                t.pos_ == "PRON" and "Yes" in t.morph.get("Clitic", [])
                for t in left_window
            )
            if has_left_clitic:
                continue
            issues.append(self._issue(
                text=text, token=token,
                rule="SPACY_MISSING_REFLEXIVE_CLITIC",
                message=(
                    f"'{token.text}' potrebbe mancare del clitico riflessivo. "
                    f"Intendevi la forma riflessiva '{reflexive_form}'? "
                    f"(es. 'Mario lava ogni mattina' → 'Mario si lava ogni mattina')"
                ),
                suggestions=[f"si {token.text}"],
            ))
        return issues

    # ------------------------------------------------------------------
    # Rule 13 – double negation / missing 'non'
    # ------------------------------------------------------------------

    def spacy_double_negation_issues(self, text: str) -> list:
        """
        Flag sentences where a negative polarity item (niente, mai…) is
        present but the finite verb has no preceding 'non'.
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for sent in doc.sents:
            tokens = list(sent)
            token_texts_lower = {t.text.lower() for t in tokens}
            npis_present = token_texts_lower & _NEGATIVE_POLARITY_WORDS
            if not npis_present:
                continue
            for token in tokens:
                if token.pos_ not in ("VERB", "AUX"):
                    continue
                if not self._is_finite_verb(token):
                    continue
                has_neg = any(
                    c.dep_ == "advmod" and c.text.lower() in ("non", "né", "ne")
                    for c in token.children
                )
                idx = token.i
                left = doc[max(0, idx - 3): idx]
                has_neg = has_neg or any(t.text.lower() == "non" for t in left)
                if not has_neg:
                    npi_sample = next(iter(npis_present))
                    issues.append(self._issue(
                        text=text, token=token,
                        rule="SPACY_DOUBLE_NEGATION",
                        message=(
                            f"Parola di polarità negativa '{npi_sample}' presente "
                            f"ma manca 'non' prima di '{token.text}'. "
                            f"L'italiano richiede la negazione concordata: 'non … {npi_sample}'. "
                            f"(es. 'Ho visto niente' → 'Non ho visto niente')"
                        ),
                        suggestions=["non " + token.text],
                    ))
                    break
        return issues

    # ------------------------------------------------------------------
    # Rule 14 – interrogative word order
    # ------------------------------------------------------------------

    def spacy_interrogative_word_order_issues(self, text: str) -> list:
        """
        In Italian questions the subject pronoun must NOT appear between
        the WH-word and the verb.
        """
        if self.nlp is None:
            return []
        _SUBJECT_PRONOUNS = {
            "io", "tu", "lui", "lei", "noi", "voi", "loro",
            "esso", "essa", "essi", "esse",
        }
        issues = []
        doc = self.nlp(text)
        for sent in doc.sents:
            if not sent.text.strip().endswith("?"):
                continue
            tokens = list(sent)
            for i, token in enumerate(tokens):
                if token.text.lower() not in _WH_WORDS:
                    continue
                window = tokens[i + 1: i + 4]
                for j, w in enumerate(window):
                    if w.text.lower() in _SUBJECT_PRONOUNS and w.dep_ in ("nsubj", "nsubj:pass"):
                        remaining = window[j + 1:]
                        verb_after = any(t.pos_ in ("VERB", "AUX") for t in remaining)
                        if verb_after or j == 0:
                            
                            issues.append(self._issue(
                                text=text, token=w,
                                rule="SPACY_INTERROGATIVE_WORD_ORDER",
                                message=(
                                    f"Nelle domande italiane il pronome soggetto "
                                    f"'{w.text}' non dovrebbe stare tra '{token.text}' e il verbo. "
                                    f"Eliminarlo o spostarlo dopo il verbo. "
                                    f"(es. 'Cosa tu fai?' → 'Cosa fai?' o 'Cosa fai tu?')"
                                ),
                               
                            ))
                            break
        return issues

    # ------------------------------------------------------------------
    # Rule 15 – gerund subject mismatch
    # ------------------------------------------------------------------

    def spacy_gerund_subject_mismatch(self, text: str) -> list:
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        root_subject = None
        for token in doc:
            if token.dep_ == "ROOT":
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubj:pass"):
                        root_subject = child
                        break
                break
        if root_subject is None:
            return []
        s_gender = root_subject.morph.get("Gender")
        s_number = root_subject.morph.get("Number")
        for token in doc:
            if "Ger" not in token.morph.get("VerbForm", []):
                continue
            for child in token.children:
                if child.pos_ != "ADJ":
                    continue
                a_gender = child.morph.get("Gender")
                a_number = child.morph.get("Number")
                mismatches = []
                if s_gender and a_gender and s_gender != a_gender:
                    mismatches.append("genere")
                if s_number and a_number and s_number != a_number:
                    mismatches.append("numero")
                if mismatches:
                    suggestion = self._inflect_italian(child.text, child.morph.get("Gender"), child.morph.get("Number"), s_gender[0] if s_gender else None, s_number[0] if s_number else None)
                    issues.append(self._issue(
                        text=text, token=child,
                        rule="SPACY_GERUND_SUBJECT_MISMATCH",
                        message=(
                            f"Accordo gerundio-soggetto ({' e '.join(mismatches)}): "
                            f"'{child.text}' non concorda con il soggetto principale "
                            f"'{root_subject.text}'. "
                            f"(es. 'Essendo stanca, lui uscì' → 'Essendo stanco, lui uscì')"
                        ),
                        suggestions=[suggestion] if suggestion else [],
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 16 – modal + non-infinitive
    # ------------------------------------------------------------------

    def spacy_modal_infinitive_issues(self, text: str) -> list:
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)
        for token in doc:
            if token.pos_ not in ("VERB", "AUX"):
                continue
            if token.lemma_.lower() not in _MODAL_VERBS:
                continue
            for child in token.children:
                if child.dep_ not in ("xcomp", "ccomp", "obj"):
                    continue
                if child.pos_ not in ("VERB", "AUX"):
                    continue
                verb_form = child.morph.get("VerbForm")
                if not verb_form:
                    continue
                if "Inf" not in verb_form:
                    wrong_form = verb_form[0] if verb_form else "forma non infinitiva"
                    lemma = child.lemma_
                    infinitive = lemma if lemma.endswith("re") else lemma + "re"
                    issues.append(self._issue(
                        text=text, token=child,
                        rule="SPACY_MODAL_INFINITIVE",
                        message=(
                            f"Il verbo modale '{token.text}' richiede l'infinito, "
                            f"ma '{child.text}' è un {wrong_form}. "
                            f"(es. 'Voglio andati' → 'Voglio andare')"
                        ),
                        suggestions=[infinitive],
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 17 – wrong auxiliary (avere vs essere) — NEW
    # ------------------------------------------------------------------

    def spacy_wrong_auxiliary_issues(self, text: str) -> list:
        """
        Detect cases where a verb that requires ESSERE is used with AVERE
        in compound tenses, or vice versa.

        Example: 'Ho andato' → 'Sono andato'
                 'Sono mangiato' → 'Ho mangiato'

        Dual-auxiliary verbs are skipped because their auxiliary depends
        on transitivity and would produce too many false positives.
        """
        if self.nlp is None:
            return []
        issues = []
        doc = self.nlp(text)

        for token in doc:
            if not self._is_past_participle(token):
                continue
            if token.lemma_.lower() in ("essere", "stare"):
                continue
            if token.lemma_.lower() in _DUAL_AUXILIARY_VERBS:
                continue

            aux_tokens = [child for child in token.children if child.dep_ == "aux"]
            aux_lemmas = {child.lemma_.lower() for child in aux_tokens}
            if not aux_lemmas:
                continue

            verb_lemma = token.lemma_.lower()
            needs_essere = verb_lemma in _ESSERE_VERBS

            if needs_essere and "avere" in aux_lemmas and "essere" not in aux_lemmas:
                issues.append(self._issue(
                    text=text, token=token,
                    rule="SPACY_WRONG_AUXILIARY",
                    message=(
                        f"'{verb_lemma}' richiede l'ausiliare 'essere', "
                        f"non 'avere'. "
                        f"(es. 'Ho andato' → 'Sono andato')"
                    ),
                    suggestions=[self._suggest_wrong_auxiliary_phrase(aux_tokens[0], token, "essere") if aux_tokens else "essere"],
                ))
            elif not needs_essere and "essere" in aux_lemmas and "avere" not in aux_lemmas:
                # Only flag if the verb is clearly transitive (has an obj child)
                has_obj = any(c.dep_ in ("obj", "iobj") for c in token.children)
                if has_obj:
                    issues.append(self._issue(
                        text=text, token=token,
                        rule="SPACY_WRONG_AUXILIARY",
                        message=(
                            f"'{verb_lemma}' usato transitivamente richiede l'ausiliare 'avere', "
                            f"non 'essere'. "
                            f"(es. 'Sono mangiato la pizza' → 'Ho mangiato la pizza')"
                        ),
                        suggestions=[self._suggest_wrong_auxiliary_phrase(aux_tokens[0], token, "avere") if aux_tokens else "avere"],
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 18 – comparative construction errors — NEW
    # ------------------------------------------------------------------

    def spacy_comparative_issues(self, text: str) -> list:
        """
        Detect common errors in Italian comparatives:
        - 'più … di' vs 'più … che' confusion
          Rule: use 'di' when comparing two different nouns/pronouns with
          the same adjective. Use 'che' when comparing two adjectives,
          verbs, adverbs or prepositional phrases about the same noun.
        - 'più migliore', 'più peggiore', 'più maggiore', 'più minore'
          (double comparative — redundant 'più' before already-comparative adj)
        """
        if self.nlp is None:
            return []

        _ALREADY_COMPARATIVE = {
            "migliore", "peggiore", "maggiore", "minore",
            "superiore", "inferiore", "anteriore", "posteriore",
        }

        issues = []
        doc = self.nlp(text)
        tokens = list(doc)

        for i, token in enumerate(tokens):
            # Double comparative: 'più' + already-comparative adjective
            if token.text.lower() == "più" and i + 1 < len(tokens):
                next_tok = tokens[i + 1]
                if next_tok.lemma_.lower() in _ALREADY_COMPARATIVE:
                    issues.append(self._issue(
                        text=text, token=token,
                        rule="SPACY_DOUBLE_COMPARATIVE",
                        message=(
                            f"Doppio comparativo: '{token.text} {next_tok.text}' è ridondante. "
                            f"'{next_tok.text}' è già un comparativo. "
                            f"(es. 'più migliore' → 'migliore')"
                        ),
                        suggestions=[next_tok.text],
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 19 – congiuntivo after verbs requiring it — NEW
    # ------------------------------------------------------------------

    def spacy_missing_subjunctive_issues(self, text: str) -> list:
        """
        Detect indicative mood used where congiuntivo is required.
        Triggered when verbs of opinion/doubt/wish/fear introduce a
        subordinate clause with 'che' but the subordinate verb is indicative.

        This is a heuristic — spaCy's mood tagging is imperfect for Italian,
        so we only flag high-confidence cases.
        """
        if self.nlp is None:
            return []

        _SUBJ_TRIGGERS = {
            "volere", "sperare", "credere", "pensare", "dubitare",
            "temere", "desiderare", "preferire", "augurarsi",
            "bisognare", "occorrere", "sembrare", "parere",
            "essere necessario", "essere importante", "essere possibile",
        }

        issues = []
        doc = self.nlp(text)

        for token in doc:
            if token.lemma_.lower() not in _SUBJ_TRIGGERS:
                continue
            # Look for a 'che' complementizer child leading to a ccomp
            for child in token.children:
                if child.dep_ not in ("ccomp", "xcomp"):
                    continue
                if child.pos_ not in ("VERB", "AUX"):
                    continue
                # Check if subordinate verb is indicative (should be subjunctive)
                mood = child.morph.get("Mood", [])
                if "Ind" in mood:
                    # Check there is a 'che' token between the trigger and the child
                    start = min(token.i, child.i)
                    end = max(token.i, child.i)
                    has_che = any(
                        t.text.lower() == "che"
                        for t in doc[start:end]
                    )
                    if has_che:
                        suggestion = self._suggest_subjunctive(child)
                        issues.append(self._issue(
                            text=text, token=child,
                            rule="SPACY_MISSING_SUBJUNCTIVE",
                            message=(
                                f"Dopo '{token.text}' + 'che' si usa il congiuntivo, "
                                f"non l'indicativo. "
                                f"'{child.text}' ({mood[0] if mood else '?'}) "
                                f"potrebbe essere al congiuntivo. "
                                f"(es. 'Penso che è tardi' → 'Penso che sia tardi')"
                            ),
                            suggestions=[suggestion] if suggestion else [],
                        ))
        return issues

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------

    def correct_text(self, text: str) -> dict:
        if not text or not text.strip():
            return {"original": text, "corrected": text, "polished": text, "matches": []}

        # LanguageTool
        lt_matches = self.tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, lt_matches)
        parsed_lt = self.parse_language_tool_matches(text, lt_matches)

        # spaCy rules
        spacy_issues = (
            self.spacy_noun_agreement_issues(text)             # 1
            + self.spacy_subject_verb_issues(text)             # 2
            + self.spacy_possessive_noun_issues(text)          # 3
            + self.spacy_aux_participle_issues(text)           # 4
            + self.spacy_article_noun_issues(text)             # 5
            + self.spacy_postnominal_adjective_issues(text)    # 6
            + self.spacy_preposition_contraction_issues(text)  # 7
            + self.spacy_verb_preposition_issues(text)         # 8
            + self.spacy_predicate_adjective_issues(text)      # 9
            + self.spacy_clitic_agreement_issues(text)         # 10
            + self.spacy_partitive_article_issues(text)        # 11
            + self.spacy_missing_reflexive_clitic(text)        # 12
            + self.spacy_double_negation_issues(text)          # 13
            + self.spacy_interrogative_word_order_issues(text) # 14
            + self.spacy_gerund_subject_mismatch(text)         # 15
            + self.spacy_modal_infinitive_issues(text)         # 16
            + self.spacy_wrong_auxiliary_issues(text)          # 17
            + self.spacy_comparative_issues(text)              # 18
            + self.spacy_missing_subjunctive_issues(text)      # 19
        )

        all_matches = parsed_lt + spacy_issues

        # Deduplication — keep highest-priority issue per character offset
        _GENERIC_RULES = {"SPACY_NOUN_AGREEMENT", "SPACY_POSTNOMINAL_ADJ_AGREEMENT"}

        def _priority(issue: dict) -> int:
            if issue["source"] == "LanguageTool":
                return 0
            if issue["rule"] in _GENERIC_RULES:
                return 1
            return 2

        best: dict[int, dict] = {}
        for issue in all_matches:
            offset = issue["offset"]
            if offset not in best or _priority(issue) > _priority(best[offset]):
                best[offset] = issue

        seen_offsets: set = set()
        deduped: list[dict] = []
        for issue in all_matches:
            offset = issue["offset"]
            if offset in seen_offsets:
                continue
            if best[offset] is issue:
                deduped.append(issue)
                seen_offsets.add(offset)

        return {
            "original": text,
            "corrected": corrected_text,
            "polished": corrected_text,
            "matches": deduped,
        }