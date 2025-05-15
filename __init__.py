from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_workshop.intents import IntentBuilder
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill


DEFAULT_SETTINGS = {
    "log_level": "WARNING"
}


class HelloWorldSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        """The __init__ method is called when the Skill is first constructed.
        Note that self.bus, self.skill_id, self.settings, and
        other base class settings are only available after the call to super().
        """
        super().__init__(*args, **kwargs)
        # be aware that below is executed after `initialize`
        self.override = True

    @classproperty
    def runtime_requirements(self):
        # if this isn't defined the skill will
        # only load if there is internet
        return RuntimeRequirements(
            internet_before_load=False,
            network_before_load=False,
            gui_before_load=False,
            requires_internet=False,
            requires_network=False,
            requires_gui=False,
            no_internet_fallback=True,
            no_network_fallback=True,
            no_gui_fallback=True,
        )
    
    def initialize(self):
        """Performs any final setup of the Skill, for instance to register
        handlers for events that the Skill will respond to.
        This is a good place to load and pre-process any data needed by your Skill.
        """
        # This initializes a settings dictionary that the skill can use to
        # store and retrieve settings. The skill_settings.json file will be
        # created in the location referenced by self.settings_path, which
        # defaults to ~/.config/mycroft/skills/<skill_id>
        # only new keys will be added, existing keys will not be overwritten
        self.settings.merge(DEFAULT_SETTINGS, new_only=True)
        # set a callback to be called when settings are changed
        self.settings_change_callback = self.on_settings_changed
        # (custom) event handler setup example
        # below is a custom event, system event specs found at
        # https://openvoiceos.github.io/message_spec/
        # this can be tested using `mana` (https://github.com/NeonGeckoCom/neon-mana-utils)
        # `mana send-message hello.world`
        self.add_event("hello.world", self.handle_hello_world_intent)
        self.my_var = "hello world"

    def on_settings_changed(self):
        """This method is called when the skill settings are changed."""
        LOG.info("Settings changed!")

    @property
    def log_level(self):
        """Dynamically get the 'log_level' value from the skill settings file.
        If it doesn't exist, return the default value.
        This will reflect live changes to settings.json files (local or from backend)
        """
        return self.settings.get("log_level", "INFO")

    @intent_handler(IntentBuilder("ThankYouIntent").require("ThankYouKeyword"))
    def handle_thank_you_intent(self, message):
        """This is an Adapt intent handler, it is triggered by a keyword."""
        self.speak_dialog("welcome")

    @intent_handler(IntentBuilder("HelloWorldIntent").require("HelloWorldKeyword"))
    def handle_hello_world_intent(self, message):
        """
        speak_dialog() is an OVOS skill method that safely handles
        formatting and speaking a dialog file and its translated dialog
        back to the user.
        """
        # wait=True will block the message bus until the dialog is finished
        self.speak_dialog("hello.world", wait=True)
        LOG.debug("'hello world' TTS finished")
        # this would speak the string without translation
        # self.speak("hello world")

    @intent_handler("Greetings.intent")
    def handle_greetings(self, message):
        self.speak_dialog("hello")

    @intent_handler("HowAreYou.intent")
    def handle_how_are_you_intent(self, message):
        """This is a Padatious intent handler.
        It is triggered using a list of sample phrases."""
        self.speak_dialog("how.are.you")
        LOG.info("There are five types of log messages: 'info, debug, warning, error, and exception.")
        # Skills can log useful information. These will appear in the CLI and
        # in the skills.log file under ~/.mycroft/logs. LOG.info() is the most
        # common log level, but it is recommended to use the others when
        # appropriate:
        # LOG.debug() - Messages useful for developers to debug the skill
        # LOG.warning() - Indicates something unexpected happened, but the skill
        #                 can recover
        # LOG.error() - Indicates a recoverable error
        # LOG.exception() - Indicates an exception that causes the skill to crash
        #                  and is non-recoverable
        if self.log_level == "WARNING":
            LOG.warning("To be able to see debug logs, you need to change the 'log_level' setting to 'DEBUG' in the core configuration (mycroft.conf)")


    def stop(self) -> bool:
        """Optional action to take when "stop" is requested by the user.
        This method should return True if it stopped something or
        False (or None) otherwise.
        If not relevant to your skill, feel free to remove.
        """
        return False
