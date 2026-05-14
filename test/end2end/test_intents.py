# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""End-to-end intent tests for ovos-skill-hello-world.

Cases live as plain text under ``test/end2end/cases/<lang>/`` — see
``ovoscope.intent_cases`` for the full file-layout contract. Adding a
phrase, intent or whole new language is a pure text edit; no Python
changes needed.

Only the Padatious-style ``.intent`` handlers (Greetings, HowAreYou)
are covered here. The two Adapt keyword intents (ThankYouIntent,
HelloWorldIntent) remain exercised by ``test/test_helloworld.py``.
"""
from pathlib import Path

from ovoscope import register_intent_case_tests

SKILL_ID = "ovos-skill-hello-world.openvoiceos"

HANDLERS = {
    "Greetings.intent": "HelloWorldSkill.handle_greetings",
    "HowAreYou.intent": "HelloWorldSkill.handle_how_are_you_intent",
}

# Generates TestPadatious / TestPadacioso / TestM2V / TestDefaultPipeline
# in this module's namespace, each with one method per (lang, utterance).
register_intent_case_tests(
    globals(),
    skill_id=SKILL_ID,
    handlers=HANDLERS,
    cases_dir=Path(__file__).parent / "cases",
)

# Marker consumed by ovoscope's auto-discovery hook.
ovoscope_intent_cases = dict(skill_id=SKILL_ID, handlers=HANDLERS)
_ovoscope_intent_cases_registered = True
