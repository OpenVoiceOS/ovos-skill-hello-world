"""Local pytest config for the end2end suite.

1. If ovoscope isn't installed (e.g. the build-tests workflow), skip
   collecting anything in this directory so pytest doesn't error on the
   ``from ovoscope import ...`` line.

2. When ovoscope IS available, inject sensible defaults for the
   accuracy reporter flags (tolerant mode + JSON + Markdown + a
   generous floor).
"""
from __future__ import annotations

try:
    import ovoscope  # noqa: F401
except ImportError:  # pragma: no cover - exercised only in CI
    collect_ignore_glob = ["*.py"]


def pytest_configure(config):
    try:
        config.getoption("--ovoscope-accuracy-tolerant")
    except (ValueError, KeyError):
        return

    config.option.ovoscope_accuracy_tolerant = True
    if not config.option.ovoscope_accuracy_report:
        config.option.ovoscope_accuracy_report = "intent-accuracy.json"
    if (hasattr(config.option, "ovoscope_accuracy_md")
            and not config.option.ovoscope_accuracy_md):
        config.option.ovoscope_accuracy_md = "intent-accuracy.md"
    if config.option.ovoscope_accuracy_min is None:
        config.option.ovoscope_accuracy_min = 0.5
