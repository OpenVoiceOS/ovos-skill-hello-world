"""Golden-utterance end-to-end coverage for ovos-skill-hello-world (en-US).

The master ovoscope corpus carries no rows for
``ovos-skill-hello-world.openvoiceos``, so ``golden_utterances.jsonl`` is
derived entirely from this skill's own intent templates: ``HelloWorldIntent``,
``ThankYouIntent``, ``Greetings`` and ``HowAreYou`` (all Padatious/Padacioso,
phrase-based intent files).

Every row is asserted via the ``ovos.intent.matched`` bus message's
``data.intent_name`` field, confirmed present in this skill's message
stream by the existing ``test_helloworld.py`` (a full ordered-sequence
``End2EndTest`` that already asserts ``SpecMessage.INTENT_MATCHED`` with
``data.intent_name`` -- this suite reuses that confirmed contract).

Run:
    uv run pytest test/end2end/test_golden_utterances.py -v
"""
import json
from pathlib import Path

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-hello-world.openvoiceos"
LANG = "en-US"

_PIPELINE = [
    "ovos-adapt-pipeline-plugin-high",
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-adapt-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-adapt-pipeline-plugin-low",
]

GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"

# Confusables from other skills' domains, picked for lexical overlap with
# greeting/gratitude/small-talk phrasing.
NEGATIVE_UTTERANCES = [
    ("what's the weather", "ovos-skill-weather.openvoiceos"),
    ("play some music", "ovos-skill-music.openvoiceos"),
    ("who are you", "ovos-skill-personal.openvoiceos"),
    ("what is your name", "ovos-skill-personal.openvoiceos"),
    ("set a timer for 5 minutes", "ovos-skill-alerts.openvoiceos"),
    ("tell me a joke", "skill-icanhazdadjokes.openvoiceos"),
    ("search the web for cats", "ovos-skill-ddg.openvoiceos"),
]


def _load_golden_rows():
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


GOLDEN_ROWS = [pytest.param(r, id=r["utterance"]) for r in _load_golden_rows()]


@pytest.fixture(scope="module")
def minicroft():
    mc = get_minicroft([SKILL_ID])
    yield mc
    mc.stop()


def _capture(mc, text, session_id):
    session = Session(session_id)
    session.lang = LANG
    session.pipeline = list(_PIPELINE)
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc)
    capture.capture(utterance, timeout=30)
    return capture.finish()


@pytest.mark.timeout(60)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=lambda r: r["utterance"])
def test_golden_utterance(minicroft, row):
    expected_intent = f"{SKILL_ID}:{row['intent_label']}"
    messages = _capture(minicroft, row["utterance"], f"golden-{row['utterance']}")
    matched = [m for m in messages if m.msg_type == "ovos.intent.matched"]
    assert matched, (
        f"{row['utterance']!r}: expected ovos.intent.matched, got "
        f"{[m.msg_type for m in messages]!r}"
    )
    names = [m.data.get("intent_name") for m in matched]
    assert expected_intent in names, (
        f"{row['utterance']!r}: expected intent_name {expected_intent!r}, got {names!r}"
    )


@pytest.mark.timeout(60)
@pytest.mark.parametrize("negative", NEGATIVE_UTTERANCES, ids=lambda n: n[0])
def test_negative_confusable_not_claimed(minicroft, negative):
    text, source_skill = negative
    messages = _capture(minicroft, text, f"negative-{text}")
    matched = [m for m in messages if m.msg_type == "ovos.intent.matched"]
    claimed = any(
        (m.data.get("intent_name") or "").startswith(f"{SKILL_ID}:") for m in matched
    )
    assert not claimed, f"{text!r} (from {source_skill}) was incorrectly claimed by {SKILL_ID}"
