import unittest
from os.path import dirname

from ovos_plugin_manager.skills import find_skill_plugins
from ovos_utils.fakebus import FakeBus
from ovos_workshop.skill_launcher import PluginSkillLoader, SkillLoader

import ovos_skill_hello_world
from ovos_skill_hello_world import HelloWorldSkill


class TestSkillLoading(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        # this skill ships its source inside a package directory, so the
        # loadable skill source dir is the package dir, not the repo root
        self.path = dirname(ovos_skill_hello_world.__file__)

    def test_from_class(self):
        bus = FakeBus()
        skill = HelloWorldSkill()
        skill._startup(bus, self.skill_id)
        self.assertEqual(skill.bus, bus)
        self.assertEqual(skill.skill_id, self.skill_id)

    def test_from_plugin(self):
        bus = FakeBus()
        for sid, plug in find_skill_plugins().items():
            if sid == self.skill_id:
                skill = plug()
                skill._startup(bus, self.skill_id)
                self.assertEqual(skill.bus, bus)
                self.assertEqual(skill.skill_id, self.skill_id)
                break
        else:
            raise RuntimeError("plugin not found")

    def test_from_loader(self):
        bus = FakeBus()
        loader = SkillLoader(bus, self.path)
        loader.load()
        self.assertEqual(loader.instance.bus, bus)
        self.assertEqual(loader.instance.root_dir, self.path)

    def test_from_plugin_loader(self):
        bus = FakeBus()
        loader = PluginSkillLoader(bus, self.skill_id)
        for sid, plug in find_skill_plugins().items():
            if sid == self.skill_id:
                loader.load(plug)
                break
        else:
            raise RuntimeError("plugin not found")
        self.assertEqual(loader.skill_id, self.skill_id)
        self.assertEqual(loader.instance.bus, bus)
        self.assertEqual(loader.instance.skill_id, self.skill_id)
