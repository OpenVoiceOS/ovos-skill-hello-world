#!/usr/bin/env python3
import os
from os import walk, path

from setuptools import setup

URL = "https://github.com/OpenVoiceOS/ovos-skill-hello-world"
SKILL_CLAZZ = "HelloWorldSkill"  # needs to match __init__.py class name
PYPI_NAME = "ovos-skill-hello-world"  # pip install PYPI_NAME
SKILL_PKG = PYPI_NAME.lower().replace('-', '_')  # import name

SKILL_AUTHOR, SKILL_NAME = URL.split(".com/")[-1].split("/")  # derived from github url to ensure standard skill_id
PLUGIN_ENTRY_POINT = f'{SKILL_NAME.lower()}.{SKILL_AUTHOR.lower()}={SKILL_PKG}:{SKILL_CLAZZ}'


def find_resource_files():
    resource_base_dirs = ("locale",)
    base_dir = path.join(os.path.dirname(__file__), SKILL_PKG)
    package_data = ["*.json"]

    for res in resource_base_dirs:
        res_dir = path.join(base_dir, res)
        if path.isdir(res_dir):
            for (directory, _, files) in walk(res_dir):
                if files:
                    relative_dir = directory.replace(base_dir + os.sep, "")
                    package_data.append(path.join(relative_dir, "*"))
    return package_data


with open(path.join(path.abspath(path.dirname(__file__)), "README.md"), "r") as f:
    long_description = f.read()


def get_version():
    """ Find the version of this skill"""
    version_file = os.path.join(os.path.dirname(__file__), SKILL_PKG, 'version.py')
    major, minor, build, alpha = (None, None, None, None)
    with open(version_file) as f:
        for line in f:
            if 'VERSION_MAJOR' in line:
                major = line.split('=')[1].strip()
            elif 'VERSION_MINOR' in line:
                minor = line.split('=')[1].strip()
            elif 'VERSION_BUILD' in line:
                build = line.split('=')[1].strip()
            elif 'VERSION_ALPHA' in line:
                alpha = line.split('=')[1].strip()

            if ((major and minor and build and alpha) or
                    '# END_VERSION_BLOCK' in line):
                break
    version = f"{major}.{minor}.{build}"
    if int(alpha):
        version += f"a{alpha}"
    return version


setup(
    name=PYPI_NAME,
    version=get_version(),
    description='OVOS hello world skill plugin',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    author=SKILL_AUTHOR,
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    packages=[SKILL_PKG],
    package_data={SKILL_PKG: find_resource_files()},
    include_package_data=True,
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
