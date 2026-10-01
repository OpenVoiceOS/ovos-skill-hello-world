"""Canary for gh-automations#166 (T-6656). Not for merge.

pytest 9 gives a unittest test that runs ``self.subTest`` the outcome
"subtests passed". This file holds one test whose subtests all pass and one
whose second subtest fails, so the ovoscope PR-comment section is exercised
on both at once:

- ``TestCanaryAllSubtestsPass`` must read as a pass, where the old formatter
  read it as a failure with the pytest-xdist worker banner as its body.
- ``TestCanaryOneSubtestFails`` must read as one failing subtest, named with
  its assertion text, where the old formatter lost it.
"""
import unittest


class TestCanaryAllSubtestsPass(unittest.TestCase):
    def test_every_subtest_passes(self):
        for lang in ("en-US", "de-DE", "pt-PT", "ca-ES", "fr-FR"):
            with self.subTest(lang=lang):
                self.assertEqual(len(lang), 5)

    def test_plain_pass(self):
        self.assertTrue(True)


class TestCanaryOneSubtestFails(unittest.TestCase):
    def test_second_subtest_fails(self):
        for lang in ("en-US", "de-DE", "pt-PT"):
            with self.subTest(lang=lang):
                self.assertNotEqual(lang, "de-DE",
                                    "canary: deliberate subtest failure")
