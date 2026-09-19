"""Multilingual golden-utterance end-to-end coverage for
ovos-skill-hello-world.

Every locale under ``ovos_skill_hello_world/locale/`` that ships
``intents/`` files (Padatious/Padacioso phrase templates, not Adapt
vocab) gets its own ``golden_utterances_<lang>.jsonl``. Each row's
utterance is copied verbatim from that locale's own
``<Intent>.intent`` file -- no translation and no drafted prose, since
the skill's shipped intent templates already are native-language
sample phrases. Three distinct lines are used per intent per locale
(a short one, the longest/most elaborate one carrying extra filler
words, and a third distinct one) when the locale's own file ships at
least three; where it ships fewer, all of them are used and the
shortfall is a locale coverage gap, not a row invented to hit a quota.

One ``MiniCroft`` is booted per locale (mirrors
ovos-skill-date-time/test/end2end/test_intents_it_it.py on dev:
``get_minicroft([SKILL_ID], max_wait=150, lang=LANG)`` with the
padacioso high/medium/low pipeline), class-scoped and torn down after
that locale's rows run, rather than one shared MiniCroft carrying every
locale as a secondary language.

Run:
    uv run pytest test/end2end/test_golden_utterances_multilang.py -v
"""
import json
from pathlib import Path
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-hello-world.openvoiceos"

PIPELINE = [
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-padatious-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-low",
]

END2END_DIR = Path(__file__).parent

LANGS = [
    "en-US", "ca-ES", "cs-CZ", "da-DK", "de-DE", "el-GR", "es-ES",
    "eu-ES", "fa-IR", "fr-FR", "gl-ES", "hu-HU", "it-IT", "kab",
    "nl-NL", "oc-FR", "pl-PL", "pt-BR", "pt-PT", "ro-RO", "ru-RU",
    "sv-SE", "tr-TR",
]

NEGATIVE_UTTERANCES = [
    ("what's the weather", "en-US", "ovos-skill-weather.openvoiceos"),
    ("set a timer for 5 minutes", "en-US", "ovos-skill-alerts.openvoiceos"),
    ("tell me a joke", "en-US", "skill-icanhazdadjokes.openvoiceos"),
]


def _load_rows(lang):
    path = END2END_DIR / f"golden_utterances_{lang}.jsonl"
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


def _matched_names(mc, text, lang, session_id):
    session = Session(session_id)
    session.lang = lang
    session.pipeline = list(PIPELINE)
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": lang},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc)
    capture.capture(utterance, timeout=30)
    return [m.data.get("intent_name") for m in capture.finish()
            if m.msg_type == "ovos.intent.matched"]


KNOWN_BUGS = {}


def _make_locale_test_case(lang):
    rows = _load_rows(lang)
    negatives = [n for n in NEGATIVE_UTTERANCES if n[1] == lang]

    class _LocaleGoldenCase(TestCase):
        LANG = lang

        @classmethod
        def setUpClass(cls):
            cls.minicroft = get_minicroft([SKILL_ID], max_wait=150, lang=lang)

        @classmethod
        def tearDownClass(cls):
            if getattr(cls, "minicroft", None):
                cls.minicroft.stop()

        def _check_row(self, row):
            expected_intent = f"{SKILL_ID}:{row['intent_label']}"
            names = _matched_names(
                self.minicroft, row["utterance"], row["lang"],
                f"golden-{row['lang']}-{row['intent_label']}-{row['utterance']}",
            )
            matched = expected_intent in names
            bug_key = (row["lang"], row["utterance"])
            if bug_key in KNOWN_BUGS and not matched:
                self.skipTest(f"known-bug: {KNOWN_BUGS[bug_key]}")
            self.assertIn(
                expected_intent, names,
                f"[{row['lang']}] {row['utterance']!r}: expected "
                f"{expected_intent!r}, got {names!r}",
            )

        def _check_negative(self, text, source_skill):
            names = _matched_names(self.minicroft, text, lang,
                                    f"negative-{lang}-{text}")
            claimed = any((n or "").startswith(f"{SKILL_ID}:") for n in names)
            self.assertFalse(
                claimed, f"[{lang}] {text!r} was incorrectly claimed by {SKILL_ID}"
            )

    for i, row in enumerate(rows):
        def _test(self, row=row):
            self._check_row(row)
        _test.__name__ = f"test_golden_{i:03d}_{row['intent_label']}"
        setattr(_LocaleGoldenCase, _test.__name__, _test)

    for i, (text, _lang, source_skill) in enumerate(negatives):
        def _neg_test(self, text=text, source_skill=source_skill):
            self._check_negative(text, source_skill)
        _neg_test.__name__ = f"test_negative_{i:03d}"
        setattr(_LocaleGoldenCase, _neg_test.__name__, _neg_test)

    _LocaleGoldenCase.__name__ = f"TestGolden_{lang.replace('-', '_')}"
    _LocaleGoldenCase.__qualname__ = _LocaleGoldenCase.__name__
    return _LocaleGoldenCase


for _lang in LANGS:
    _cls = _make_locale_test_case(_lang)
    globals()[_cls.__name__] = _cls
del _lang, _cls  # for-loop variables leak into module globals; without this
# deletion pytest also collects a spurious extra test class literally named
# "_cls" (bound to whichever locale ran last), which boots a second,
# redundant MiniCroft for that locale under a different collected name.
