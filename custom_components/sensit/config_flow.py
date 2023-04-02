"""Config flow for Sensit integration integration."""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_NAME, CONF_SENSORS
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO Clean this part, use const.py ? 
CONF_URL = "backend_url"
CONF_DEVICE_NAME = "name"
CONF_DEVICE_ID = "device_id"
CONF_VERSION = "version"
CONF_MODE = "mode"
SENSIT_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_NAME, default=("DEVICE_NAME")): cv.string,
        vol.Required(CONF_DEVICE_ID, default=("DEVICE_ID")): cv.string,
        vol.Required(CONF_VERSION,default=1): cv.positive_int,
        vol.Optional(CONF_MODE, default="local"): cv.string,
        vol.Optional(CONF_URL, default="backend.sigfox.com"): cv.string
    }
)

class CustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sensit integration."""
    VERSION = 1
    data: Optional[Dict[str, Any]]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """ Second step, allow configuration of devices."""
        errors: dict[str, str] = {}
        if user_input is not None:
            logging.info(f"Step device - user input: str({user_input})")
            # self.data[CONF_SENSORS].append(user_input)
            # If ticked, we add another device
            # if user_input.get("add_another", False):
            #     return await self.async_step_user()

            # Create entry
            return self.async_create_entry(title=user_input.get("name", "No name"), data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=SENSIT_DEVICE_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        # Collect information on configured items and devices
        entity_registry = await async_get_registry(self.hass)
        logging.info(f"Entity registry: {str(entity_registry)}")
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        logging.info(f"Config Entries: {str(self.config_entry)}")
        logging.info(f"Entries: {str(entries)}")

        # TODO When the service has been added to the integration: allow  edition.
        options_schema = vol.Schema(
            {
                vol.Optional(CONF_DEVICE_NAME): cv.string,
                vol.Optional(CONF_MODE): cv.string,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
