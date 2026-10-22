from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_spec_tools.messages import SpecMessage
from ovos_utils.log import LOG
from ovoscope import CaptureSession, DEFAULT_IGNORED, End2EndTest, get_minicroft


# Messages whose presence in a capture depends on the environment rather than
# on the skill. Audio output lifecycle messages come from the audio service,
# which a minimal test extra does not install.
ENVIRONMENTAL = ["recognizer_loop:audio_output_start",
                 "recognizer_loop:audio_output_end"]
IGNORED = DEFAULT_IGNORED + ENVIRONMENTAL


class TestPadaciosoHelloWorldIntent(TestCase):
    """``greetings`` is an intent file, not an Adapt keyword rule, so
    it is reachable via the padacioso pipeline and unreachable via an
    adapt-only pipeline."""

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])  # reuse for speed, but beware if skills keeping internal state

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_padacioso_match(self):
        session = Session("123")
        session.pipeline = ["ovos-padacioso-pipeline-plugin-high"]
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
                              "intent_name": f"{self.skill_id}:greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_START,
                        data={"skill_id": self.skill_id,
                              "intent_name": "greetings"},
                        context={"skill_id": self.skill_id}),
                Message(f"{self.skill_id}:greetings",
                        data={"utterance": "hello world", "lang": "en-US"},
                        context={"skill_id": self.skill_id}),
                Message("mycroft.skill.handler.start",
                        data={"name": "HelloWorldSkill.handle_greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.SPEAK,
                        data={"utterance": "Hello world",
                              "lang": "en-US",
                              "expect_response": False,
                              "meta": {
                                  "dialog": "hello_world",
                                  "data": {},
                                  "skill": self.skill_id
                              }},
                        context={"skill_id": self.skill_id}),
                Message("mycroft.skill.handler.complete",
                        data={"name": "HelloWorldSkill.handle_greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_COMPLETE,
                        data={"skill_id": self.skill_id,
                              "intent_name": "greetings"},
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


class TestPadaciosoIntent(TestCase):

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_padacioso_match(self):
        session = Session("123")
        session.pipeline = ["ovos-padacioso-pipeline-plugin-high"]
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
                              "intent_name": f"{self.skill_id}:greetings"},
                        context={"skill_id": self.skill_id}),
                Message(SpecMessage.INTENT_HANDLER_START,
                        data={"skill_id": self.skill_id,
                              "intent_name": "greetings"},
                        context={"skill_id": self.skill_id}),
                Message(f"{self.skill_id}:greetings",
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
                              "intent_name": "greetings"},
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
    """``greetings`` and ``thank_you_intent`` are intent files (see
    ``locale/*/intents/greetings.intent`` and
    ``thank_you_intent.intent``), not Adapt keyword rules. A pipeline stack
    with no Adapt stage at all must still match them, which an Adapt-only
    keyword intent never would."""

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-hello-world.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _matched_intent_names(self, utterance):
        session = Session("123")
        session.pipeline = ["ovos-padacioso-pipeline-plugin-high"]
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
        self.assertIn(f"{self.skill_id}:greetings", names)

    def test_thank_you_matches_without_adapt(self):
        names = self._matched_intent_names("thank you")
        self.assertIn(f"{self.skill_id}:thank_you_intent", names)



class TestWorldKeywordBranch(TestCase):
    """The ``hello_world_keyword.voc`` keyword decides which dialog the
    greetings intent speaks, through a real padacioso match of the utterance."""

    skill_id = "ovos-skill-hello-world.openvoiceos"

    def _spoken_dialog(self, utterance, lang):
        minicroft = get_minicroft([self.skill_id], lang=lang)
        try:
            session = Session("123")
            session.lang = lang
            session.pipeline = ["ovos-padacioso-pipeline-plugin-high"]
            message = Message("recognizer_loop:utterance",
                              {"utterances": [utterance], "lang": lang},
                              {"session": session.serialize(), "source": "A", "destination": "B"})
            capture = CaptureSession(minicroft)
            capture.capture(message, timeout=15)
            messages = capture.finish()
        finally:
            minicroft.stop()
        matched = [m.data.get("intent_name") for m in messages
                   if m.msg_type == SpecMessage.INTENT_MATCHED]
        self.assertEqual(matched, [f"{self.skill_id}:greetings"])
        spoken = [m for m in messages if m.msg_type == SpecMessage.SPEAK]
        self.assertEqual(len(spoken), 1)
        return spoken[0].data["meta"]["dialog"]

    def test_en_us(self):
        self.assertEqual(self._spoken_dialog("hello world", "en-US"), "hello_world")
        self.assertEqual(self._spoken_dialog("hello", "en-US"), "hello")

    def test_es_es(self):
        self.assertEqual(self._spoken_dialog("hola mundo", "es-ES"), "hello_world")
        self.assertEqual(self._spoken_dialog("hola", "es-ES"), "hello")
