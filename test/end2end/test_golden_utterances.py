"""Golden rows in every locale route to their intent on the m2v pipeline.

For each ``golden_utterances_<lang>.jsonl`` in this directory, one MiniCroft
loads the real skill in that language on the m2v prototype pipeline, the
model2vec engine built at boot from the skill's own ``.intent`` files. Each
row's utterance goes through that pipeline's high, medium and low tiers in
order, and the row passes when the first tier to match names its
``intent_label``. The engine embeds the utterance, so a row that no template
spells out word for word still matches when it means the same thing.

Each ``negative_utterances_<lang>.jsonl`` holds requests for other skills.
They run on the same pipeline and must not match any intent of this skill.

Each locale must match at least ``MIN_MATCH_RATE`` of its golden rows, and at
least ``MIN_MATCHED_ROWS_PER_INTENT`` rows of each intent. A locale in
``GOLDEN_LOCALE_GAPS`` below the rate is an expected failure, but it still
fails when an intent not in ``GOLDEN_INTENT_GAPS`` has no matched row or when
its rate falls more than ``GAP_TOLERANCE`` below the rate measured for its
entry; an entry whose rate reaches ``MIN_MATCH_RATE``, or whose intent matches
a row again, fails too. A negative row that
matches this skill fails the locale, unless ``NEGATIVE_KNOWN_CLAIMS`` lists
that claim. All rows run, including rows marked ``needs_manual`` or
``machine_generated``, and the test prints every row that misses with the
intent that matched instead.
"""
import json
from pathlib import Path

import pytest
from ovos_bus_client.message import Message
from ovoscope import M2V_PUBLISHED_MODEL, get_m2v_minicroft
from ovoscope.golden_minicroft import warm_m2v_models

SKILL_ID = "ovos-skill-hello-world.openvoiceos"
M2V_PROTOTYPE = "ovos-m2v-prototype-pipeline"
TIERS = ("high", "medium", "low")
# m2v gives some rows a different answer on each boot, so the test gates on
# the share of rows that match per locale, not on each row.
MIN_MATCH_RATE = 0.8
# A locale also fails when any of its intents has fewer matched rows than this.
MIN_MATCHED_ROWS_PER_INTENT = 1
END2END_DIR = Path(__file__).parent
# Locales below MIN_MATCH_RATE on the published m2v model, mapped to the rate
# measured there (identical in three runs) and the reason. The rate check
# becomes an expected failure for them, and fails once the rate reaches
# MIN_MATCH_RATE: the stale entry goes. The per-intent floor still applies, and
# so does a drop of more than GAP_TOLERANCE below the measured rate.
_RETRAIN = "published m2v model predates these templates; remove after retrain"
GOLDEN_LOCALE_GAPS = {
    "cs-CZ": (0.75, f"{_RETRAIN}; the four how_are_you rows match nothing"),
    "es-CO": (0.625, f"{_RETRAIN}; match nothing: 'hace rato que no te veía', 'quiubo', "
                     "'cómo te sientes', 'cómo amaneciste', 'mil gracias, muy amable', "
                     "'te agradezco un montón'"),
    "tr-TR": (0.706, f"{_RETRAIN}; match nothing: 'görüşmeyeli çok oldu', "
                     "'herkese iyi günler', 'selam herkese', 'iyi misin', "
                     "'yardımın için teşekkürler'"),
}
# (locale, intent) pairs that the per-intent floor skips. Each pair keeps its
# rows in the rate. The test fails once the intent matches a row: the stale
# entry goes.
GOLDEN_INTENT_GAPS = {
    ("cs-CZ", "how_are_you"): f"{_RETRAIN}; measured: none of its four rows matches "
                              "('jak to dneska jde', 'jak ses dneska měl', "
                              "'daří se ti dobře', 'je ti dobře')",
}
GAP_TOLERANCE = 0.10
# Locales whose negative rows the published m2v model cannot separate from
# this skill's intents, mapped to the measured reason.
NEGATIVE_ENGINE_GAPS = {}
# Negative rows that m2v claimed for this skill in two separate runs, as
# {lang: {utterance: claimed_intent}}. A listed claim is allowed, not
# required, so a row that flips between boots does not fail the test. Any
# other claim fails the locale.
NEGATIVE_KNOWN_CLAIMS = {
    "es-ES": {"qué tiempo hará mañana": "greetings"},
    "nl-NL": {"wat voor weer wordt het morgen": "greetings"},
}


def _rows_by_lang(prefix):
    rows = {}
    for path in sorted(END2END_DIR.glob(f"{prefix}_*.jsonl")):
        lang = path.stem.removeprefix(f"{prefix}_")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                row = json.loads(line)
                assert row["lang"] == lang, f"{path.name}:{number} has lang {row['lang']!r}"
                rows.setdefault(lang, []).append(row)
    return rows


ROWS = _rows_by_lang("golden_utterances")
NEGATIVE_ROWS = _rows_by_lang("negative_utterances")


def _matched_intent(engine, utterance, lang):
    message = Message("recognizer_loop:utterance",
                      {"utterances": [utterance], "lang": lang}, {"lang": lang})
    match = next(filter(None, (getattr(engine, f"match_{tier}")([utterance], lang, message)
                               for tier in TIERS)), None)
    return match.match_type if match else None


def _match_all(lang, rows):
    """Boot the skill on m2v in ``lang`` and return the intent each row matches."""
    minicroft = get_m2v_minicroft([SKILL_ID], model=M2V_PUBLISHED_MODEL,
                                  lang=lang, classifier=False)
    try:
        warm_m2v_models(minicroft)
        engine = minicroft.intents.pipeline_plugins[M2V_PROTOTYPE]
        return [_matched_intent(engine, row["utterance"], lang) for row in rows]
    finally:
        minicroft.stop()


@pytest.mark.timeout(900)
@pytest.mark.parametrize("lang", sorted(ROWS))
def test_golden_rows_match_their_intent(lang):
    rows = ROWS[lang]
    matched = _match_all(lang, rows)
    misses = []
    hits = {row["intent_label"]: 0 for row in rows}
    for row, got in zip(rows, matched):
        if got == f"{SKILL_ID}:{row['intent_label']}":
            hits[row["intent_label"]] += 1
        else:
            misses.append(f"{row['utterance']!r}: expected {row['intent_label']}, got {got}")
    starved = sorted(label for label, count in hits.items()
                     if count < MIN_MATCHED_ROWS_PER_INTENT
                     and (lang, label) not in GOLDEN_INTENT_GAPS)
    healed = sorted(label for label, count in hits.items()
                    if count >= MIN_MATCHED_ROWS_PER_INTENT
                    and (lang, label) in GOLDEN_INTENT_GAPS)
    rate = 1 - len(misses) / len(rows)
    print(f"[{lang}] {rate:.1%} of {len(rows)} rows match", *misses, sep="\n  ")
    assert not starved, (
        f"[{lang}] intents below {MIN_MATCHED_ROWS_PER_INTENT} matched rows: {starved}"
    )
    assert not healed, f"[{lang}] intents match again: remove their GOLDEN_INTENT_GAPS entries: {healed}"
    if lang in GOLDEN_LOCALE_GAPS:
        measured, reason = GOLDEN_LOCALE_GAPS[lang]
        assert rate >= measured - GAP_TOLERANCE, (
            f"[{lang}] {rate:.1%} of rows match, more than {GAP_TOLERANCE:.0%} below "
            f"the measured {measured:.1%}:\n  " + "\n  ".join(misses)
        )
        assert rate < MIN_MATCH_RATE, (
            f"[{lang}] {rate:.1%} of rows match, at the gate: remove its GOLDEN_LOCALE_GAPS entry"
        )
        pytest.xfail(f"[{lang}] {rate:.1%} of rows match, known gap: {reason}")
    assert rate >= MIN_MATCH_RATE, (
        f"[{lang}] {rate:.1%} of rows match, below {MIN_MATCH_RATE:.0%}:\n  " + "\n  ".join(misses)
    )


@pytest.mark.timeout(900)
@pytest.mark.parametrize("lang", [
    pytest.param(lang, marks=pytest.mark.xfail(reason=NEGATIVE_ENGINE_GAPS[lang]))
    if lang in NEGATIVE_ENGINE_GAPS else lang
    for lang in sorted(NEGATIVE_ROWS)
])
def test_negative_rows_match_no_skill_intent(lang):
    rows = NEGATIVE_ROWS[lang]
    known = NEGATIVE_KNOWN_CLAIMS.get(lang, {})
    matched = _match_all(lang, rows)
    claims = [(row["utterance"], got.removeprefix(f"{SKILL_ID}:"))
              for row, got in zip(rows, matched)
              if got and got.startswith(f"{SKILL_ID}:")]
    unknown = [f"{utterance!r}: matched {intent}" for utterance, intent in claims
               if known.get(utterance) != intent]
    print(f"[{lang}] {len(claims)} of {len(rows)} negative rows claimed, "
          f"{len(unknown)} not in NEGATIVE_KNOWN_CLAIMS", *unknown, sep="\n  ")
    assert not unknown, f"[{lang}] negative rows matched this skill:\n  " + "\n  ".join(unknown)


LOCALE_ROOT = END2END_DIR.parents[1] / "ovos_skill_hello_world" / "locale"


def _intent_names(locale_dir):
    return {path.name for path in locale_dir.rglob("*.intent")}


def test_every_shipping_locale_has_a_golden_file():
    golden = {p.stem.split("_", 2)[2] for p in END2END_DIR.glob("golden_utterances_*.jsonl")}
    shipping = {d.name for d in LOCALE_ROOT.iterdir() if d.is_dir() and any(d.rglob("*.intent"))}
    assert golden == shipping, f"golden files {sorted(golden ^ shipping)} differ from shipping locales"


@pytest.mark.parametrize("lang", sorted(d.name for d in LOCALE_ROOT.iterdir() if d.is_dir()))
def test_every_en_us_intent_file_exists_in_locale(lang):
    missing = _intent_names(LOCALE_ROOT / "en-US") - _intent_names(LOCALE_ROOT / lang)
    assert not missing, f"[{lang}] intent files missing: {sorted(missing)}"
