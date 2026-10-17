import json
import unittest
from os.path import dirname, join

from ovos_spec_tools.expansion import expand
from ovos_utils.fakebus import FakeBus

from ovos_skill_hello_world import HelloWorldSkill

# The template lines of greetings.intent and hello_world_intent.intent before
# they were merged, per locale.
PRE_MERGE = json.load(open(join(dirname(__file__), "pre_merge_intents.json"),
                           encoding="utf-8"))

# Greeting lines that name the world and so legitimately speak the
# hello world reply.
WORLD_GREETINGS = {"fr-FR": ["le monde"]}

# One-word hello world lines that are plain greetings; they must not speak
# the hello world reply.
BARE_GREETINGS = {
    "ca-ES": ["salutacions"], "cs-CZ": ["zdravím"], "de-DE": ["schöne grüße"],
    "el-GR": ["χαιρετίσματα"], "eu-ES": ["agurrak"], "fr-FR": ["salutations"],
    "hu-HU": ["üdv"], "it-IT": ["saluti"], "nl-NL": ["groeten"],
    "oc-FR": ["salutacions"], "pl-PL": ["witam"], "pt-PT": ["saudações"],
    "ro-RO": ["salutări"], "sv-SE": ["var hälsad"], "tr-TR": ["selamlar"],
}


def _expand(lines):
    return {e.strip() for line in lines for e in expand(line)}


class TestWorldKeyword(unittest.TestCase):
    """hello_world_keyword.voc separates the hello world requests from the
    plain greetings in every locale."""

    @classmethod
    def setUpClass(cls):
        cls.skill = HelloWorldSkill()
        cls.skill._startup(FakeBus(), "ovos-skill-hello-world.openvoiceos")

    def _matches(self, utterance, lang):
        return bool(self.skill.voc_match(utterance, "hello_world_keyword", lang=lang))

    def test_world_requests_match_and_plain_greetings_do_not(self):
        for lang, lines in sorted(PRE_MERGE.items()):
            shared = (set(lines["greetings"]) & set(lines["hello_world"])) | set(BARE_GREETINGS.get(lang, []))
            world = _expand(set(lines["hello_world"]) - shared)
            plain = _expand(set(lines["greetings"]) - shared)
            self.assertTrue(world, lang)
            with self.subTest(lang=lang):
                missed = sorted(u for u in world if not self._matches(u, lang))
                self.assertEqual(missed, [], f"{lang}: world requests without a match")
                leaked = sorted(
                    u for u in plain
                    if self._matches(u, lang)
                    and not any(w in u for w in WORLD_GREETINGS.get(lang, []))
                )
                self.assertEqual(leaked, [], f"{lang}: plain greetings that match")
