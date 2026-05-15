"""Smoke tests for HelloWorldSkill — no bus, no minicroft.

End-to-end intent routing is covered by ``test/end2end/`` (ovoscope).
This module gives the ``build-tests`` workflow something to collect
when ovoscope isn't installed.
"""
from unittest import TestCase
from unittest.mock import Mock, patch


class TestHelloWorldSkillSmoke(TestCase):

    def test_import_skill_class(self):
        from ovos_skill_hello_world import HelloWorldSkill
        self.assertTrue(callable(HelloWorldSkill))

    def test_default_settings_present(self):
        from ovos_skill_hello_world import DEFAULT_SETTINGS
        self.assertIn("log_level", DEFAULT_SETTINGS)

    def test_runtime_requirements_offline_capable(self):
        from ovos_skill_hello_world import HelloWorldSkill
        # ``runtime_requirements`` is a classproperty — read off the class.
        rr = HelloWorldSkill.runtime_requirements
        self.assertFalse(rr.requires_internet)
        self.assertFalse(rr.requires_network)
        self.assertTrue(rr.no_internet_fallback)
