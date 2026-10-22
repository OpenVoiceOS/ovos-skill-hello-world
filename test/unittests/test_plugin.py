import unittest

from ovos_plugin_manager.skills import find_skill_plugins


class TestPlugin(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.skill_id = "ovos-skill-hello-world.openvoiceos"

    def test_find_plugin(self):
        self.assertIn(self.skill_id, list(find_skill_plugins()))
