"""Every locale ships the layout en-US ships, with OVOS-INTENT-2 §2 names.

gl-ES carried ``intent/HowAreYou.intent`` beside ``intents/how_are_you.intent``.
The runtime reads ``intents/``, so the stray was never registered, and its
two phrasings were never heard. A second directory is a broken file, not a
convention, and the base name broke §2 as well. This checks both, for every
locale, so the next stray fails on the day it lands.
"""
import re
from pathlib import Path

import pytest

LOCALE = Path(__file__).resolve().parents[2] / "ovos_skill_hello_world" / "locale"
REFERENCE = LOCALE / "en-US"
COMPLIANT = re.compile(r"^[a-z0-9_]+$")
LOCALES = sorted(p.name for p in LOCALE.iterdir() if p.is_dir())


def _dirs(locale: Path) -> set:
    return {p.name for p in locale.iterdir() if p.is_dir()}


@pytest.mark.parametrize("lang", LOCALES)
def test_the_locale_ships_only_the_reference_directories(lang):
    extra = _dirs(LOCALE / lang) - _dirs(REFERENCE)
    assert not extra, (
        f"{lang} ships {sorted(extra)}, which en-US does not: a resource "
        f"directory the loader never reads")


@pytest.mark.parametrize("lang", LOCALES)
def test_every_resource_base_name_is_spec_compliant(lang):
    bad = [str(p.relative_to(LOCALE)) for p in (LOCALE / lang).rglob("*")
           if p.suffix in {".intent", ".voc", ".dialog", ".entity"}
           and not COMPLIANT.match(p.stem)]
    assert not bad, bad


def test_the_reference_ships_the_intents_directory():
    """The control: the reference layout is the one the loader reads."""
    assert "intents" in _dirs(REFERENCE)
    assert "intent" not in _dirs(REFERENCE)
