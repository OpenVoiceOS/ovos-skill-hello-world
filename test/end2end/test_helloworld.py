from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_spec_tools.messages import SpecMessage
from ovos_utils.log import LOG
from ovoscope import CaptureSession, DEFAULT_IGNORED, End2EndTest, get_minicroft

from ._wait_trained import wait_for_minicroft_ready


# Messages whose presence in a capture depends on the environment or on thread
# timing rather than on the skill.
#
# Audio output lifecycle messages come from the audio service, which a minimal
# test extra does not install.
#
# mycroft.skills.trained is the completion signal ovos-padatious emits for a
# training pass. setUp waits for it, so the utterance is never sent before the
# compile lands; it is ignored here as well because a later pass can still
# land inside a capture window and change the count. Waiting is what makes the
# intent reachable, and ignoring is what keeps the count stable.
ENVIRONMENTAL = ["recognizer_loop:audio_output_start",
                 "recognizer_loop:audio_output_end",
                 "mycroft.skills.trained"]
IGNORED = DEFAULT_IGNORED + ENVIRONMENTAL


class TestPadatiousHelloWorldIntent(TestCase):
    """``HelloWorldIntent`` is now a Padatious/Padacioso intent file, not an
    Adapt keyword rule, so it is reachable via the padatious pipeline and
    unreachable via an adapt-only pipeline."""

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])  # reuse for speed, but beware if skills keeping internal state
        wait_for_minicroft_ready(self.minicroft)

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_padatious_match(self):
        session = Session("123")
        session.pipeline = ["ovos-padatious-pipeline-plugin-high"]
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["hello world"], "lang": "en-US"},
                          {"session": session.serialize(), "source": "A", "destination": "B"})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.skill_id],
            source_message=message,
            ignore_messages=IGNORED,
            expected_messages=[
                message,
                Message(f"{self.skill_id}.activate",
                        data={},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_MATCHED,
                        data={"skill_id": self.skill_id,
                              "intent_name": f"{self.skill_id}:HelloWorldIntent"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_START,
                        data={"skill_id": self.skill_id,
                              "intent_name": "HelloWorldIntent"},
                        context={"skill_id": self.skill_id}),
                Message(f"{self.skill_id}:HelloWorldIntent",
                        data={"utterance": "hello world", "lang": "en-US"},
                        context={"skill_id": self.skill_id}),
                Message("mycroft.skill.handler.start",
                        data={"name": "HelloWorldSkill.handle_hello_world_intent"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.SPEAK,
                        data={"utterance": "Hello world",
                              "lang": "en-US",
                              "expect_response": False,
                              "meta": {
                                  "dialog": "hello.world",
                                  "data": {},
                                  "skill": self.skill_id
                              }},
                        context={"skill_id": self.skill_id}),
                Message("mycroft.skill.handler.complete",
                        data={"name": "HelloWorldSkill.handle_hello_world_intent"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_COMPLETE,
                        data={"skill_id": self.skill_id,
                              "intent_name": "HelloWorldIntent"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.UTTERANCE_HANDLED,
                        data={},
                        context={"skill_id": self.skill_id}),
            ]
        )

        test.execute(timeout=10)

    def test_adapt_no_match(self):
        session = Session("123")
        session.pipeline = ['ovos-adapt-pipeline-plugin-high']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["hello world"], "lang": "en-US"},
                          {"session": session.serialize(), "source": "A", "destination": "B"})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.skill_id],
            source_message=message,
            ignore_messages=IGNORED,
            expected_messages=[
                message,
                Message("mycroft.audio.play_sound", {"uri": "snd/error.mp3"}),
                Message(SpecMessage.INTENT_UNMATCHED, {}),
                Message(SpecMessage.UTTERANCE_HANDLED, {})
            ]
        )

        test.execute(timeout=10)


class TestPadatiousIntent(TestCase):

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])
        wait_for_minicroft_ready(self.minicroft)

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_padatious_match(self):
        session = Session("123")
        session.pipeline = ["ovos-padatious-pipeline-plugin-high"]
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["good morning"], "lang": "en-US"},
                          {"session": session.serialize(), "source": "A", "destination": "B"})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.skill_id],
            source_message=message,
            ignore_messages=IGNORED,
            expected_messages=[
                message,
                Message(f"{self.skill_id}.activate",
                        data={},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_MATCHED,
                        data={"skill_id": self.skill_id,
                              "intent_name": f"{self.skill_id}:Greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_START,
                        data={"skill_id": self.skill_id,
                              "intent_name": "Greetings"},
                        context={"skill_id": self.skill_id}),
                Message(f"{self.skill_id}:Greetings",
                        data={"utterance": "good morning", "lang": "en-US"},
                        context={"skill_id": self.skill_id}),
                Message("mycroft.skill.handler.start",
                        data={"name": "HelloWorldSkill.handle_greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.SPEAK,
                        data={"lang": "en-US",
                              "expect_response": False,
                              "meta": {
                                  "dialog": "hello",
                                  "data": {},
                                  "skill": self.skill_id
                              }},
                        context={"skill_id": self.skill_id}),
                Message("mycroft.skill.handler.complete",
                        data={"name": "HelloWorldSkill.handle_greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_COMPLETE,
                        data={"skill_id": self.skill_id,
                              "intent_name": "Greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.UTTERANCE_HANDLED,
                        data={},
                        context={"skill_id": self.skill_id}),
            ]
        )

        test.execute(timeout=10)

    def test_adapt_no_match(self):
        session = Session("123")
        session.pipeline = ['ovos-adapt-pipeline-plugin-high']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["good morning"], "lang": "en-US"},
                          {"session": session.serialize(), "source": "A", "destination": "B"})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.skill_id],
            source_message=message,
            ignore_messages=IGNORED,
            expected_messages=[
                message,
                Message("mycroft.audio.play_sound", {"uri": "snd/error.mp3"}),
                Message(SpecMessage.INTENT_UNMATCHED, {}),
                Message(SpecMessage.UTTERANCE_HANDLED, {})
            ]
        )

        test.execute(timeout=10)



class TestNoAdaptPipeline(TestCase):
    """``HelloWorldIntent`` and ``ThankYouIntent`` are Padatious/Padacioso
    intent files (see ``locale/*/intents/HelloWorldIntent.intent`` and
    ``ThankYouIntent.intent``), not Adapt keyword rules. A pipeline stack
    with no Adapt stage at all must still match them, which an Adapt-only
    keyword intent never would."""

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])
        wait_for_minicroft_ready(self.minicroft)

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _matched_intent_names(self, utterance):
        session = Session("123")
        session.pipeline = [
            "ovos-padatious-pipeline-plugin-high",
            "ovos-padacioso-pipeline-plugin-high",
        ]
        message = Message("recognizer_loop:utterance",
                          {"utterances": [utterance], "lang": "en-US"},
                          {"session": session.serialize(), "source": "A", "destination": "B"})
        capture = CaptureSession(self.minicroft)
        capture.capture(message, timeout=15)
        messages = capture.finish()
        matched = [m for m in messages if m.msg_type == SpecMessage.INTENT_MATCHED]
        return [m.data.get("intent_name") for m in matched]

    def test_hello_world_matches_without_adapt(self):
        names = self._matched_intent_names("hello world")
        self.assertIn(f"{self.skill_id}:HelloWorldIntent", names)

    def test_thank_you_matches_without_adapt(self):
        names = self._matched_intent_names("thank you")
        self.assertIn(f"{self.skill_id}:ThankYouIntent", names)
