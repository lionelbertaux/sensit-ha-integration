"""Config flow for Sensit integration integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from homeassistant.const import CONF_NAME, CONF_SENSORS


from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


CONF_URL = "backend_url"
CONF_MODE_GLOBAL = "version"


SENSIT_INTEGRATION_SCHEMA = vol.Schema({
			vol.Optional(CONF_URL, default="backend.sigfox.com"): cv.string,
			vol.Optional(CONF_MODE_GLOBAL, default="local"): cv.string,
		})

CONF_DEVICE_NAME = "name"
CONF_DEVICE_ID = "device_id"
CONF_VERSION = "version"
CONF_MODE = "mode"

SENSIT_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_VERSION): cv.positive_int,
        vol.Optional(CONF_MODE, default="local"): cv.string,
        vol.Optional("add_another"): cv.boolean
    }
)

class CustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sensit integration."""

    data: Optional[Dict[str, Any]]


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            logging.info(f"Step integration - user input: str({user_input})")
            self.data = user_input
            self.data[CONF_SENSORS] = []
            if not errors:
                return await self.async_step_device()
        return self.async_show_form(
            step_id="user", data_schema=SENSIT_INTEGRATION_SCHEMA, errors=errors
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """ Second step, allow configuration of devices."""
        errors: dict[str, str] = {}
        if user_input is not None:
            logging.info(f"Step device - user input: str({user_input})")
            self.data[CONF_SENSORS].append(user_input)
            
            # If ticked, we add another device
            if user_input.get("add_another", False):
                return await self.async_step_device()

            # Create entry
            return self.async_create_entry(title="Sensit Integration", data=self.data)

        return self.async_show_form(
            step_id="device", data_schema=SENSIT_DEVICE_SCHEMA, errors=errors
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
