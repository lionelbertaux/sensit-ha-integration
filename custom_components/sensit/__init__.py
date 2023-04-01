
import logging
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import threading
import asyncio

from homeassistant import config_entries, core


_LOGGER = logging.getLogger(__name__)

DOMAIN = "sensit"

CONF_URL = "backend_url"
CONF_MODE = "local"

CONFIG_SCHEMA = vol.Schema(
	{
		DOMAIN: vol.Schema({
			vol.Required(CONF_URL, default="backend.sigfox.com"): cv.string,
			vol.Optional(CONF_MODE, default="local"): cv.string,
		})
	},
	extra=vol.ALLOW_EXTRA,
)


# def setup(hass, config):
#     """ Only used when configuring from file
#     """
#     logging.info("basic setup")
#     conf = config[DOMAIN]
#     backend_url = conf.get(CONF_URL)
#     data_mode = conf.get(CONF_MODE)

#     hass.states.set("sensit.world", backend_url)

#     return True


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Before creating the sensors, we need to register a global service 
    #     corresponding the global configuration of the device (mode, version, ...)

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True




async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok



"""
basic integration configuration:
https://blog.thestaticturtle.fr/creating-a-custom-component-for-homeassistant/

Documentation on manigest:
https://developers.home-assistant.io/docs/creating_integration_manifest

Further steps for integration:
https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_1/

Other: https://dev.to/adafycheng/write-custom-component-for-home-assistant-4fce

"""
