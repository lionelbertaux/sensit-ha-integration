
import logging
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import threading

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sensit"

CONF_URL = "backend_url"
CONF_VERSION = "version"

CONFIG_SCHEMA = vol.Schema(
	{
		DOMAIN: vol.Schema({
			vol.Required(CONF_URL, default="backend.sigfox.com"): cv.string,
			vol.Optional(CONF_VERSION, default=2): cv.positive_int,
		})
	},
	extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    conf = config[DOMAIN]
    backend_url = conf.get(CONF_URL)
    sensit_version = conf.get(CONF_VERSION)

    hass.states.set("sensit.world", backend_url)

    return True


"""
basic integration configuration:
https://blog.thestaticturtle.fr/creating-a-custom-component-for-homeassistant/

Documentation on manigest:
https://developers.home-assistant.io/docs/creating_integration_manifest

Further steps for integration:
https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_1/

Other: https://dev.to/adafycheng/write-custom-component-for-home-assistant-4fce

"""
