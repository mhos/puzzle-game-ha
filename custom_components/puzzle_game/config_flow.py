"""Config flow for Puzzle Game integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_CONVERSATION_AGENT

_LOGGER = logging.getLogger(__name__)


async def _get_conversation_agents(hass: HomeAssistant) -> dict[str, str]:
    """Get available conversation agents."""
    agents = {"default": "Default Assistant"}

    # Simple approach: get all states that start with conversation.
    for state in hass.states.async_all("conversation"):
        entity_id = state.entity_id
        # Get friendly name from attributes, or generate from entity_id
        friendly_name = state.attributes.get("friendly_name")
        if not friendly_name:
            friendly_name = entity_id.replace("conversation.", "").replace("_", " ").title()
        agents[entity_id] = friendly_name

    return agents


class PuzzleGameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Puzzle Game."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Puzzle Game",
                data={
                    CONF_CONVERSATION_AGENT: user_input.get(CONF_CONVERSATION_AGENT, "default"),
                },
            )

        # Get available conversation agents
        agents = await _get_conversation_agents(self.hass)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CONVERSATION_AGENT,
                        default="default",
                    ): vol.In(agents),
                }
            ),
            description_placeholders={
                "note": "Select which AI assistant to use for generating puzzles. "
                        "The default uses your configured Home Assistant conversation agent."
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PuzzleGameOptionsFlow:
        """Get the options flow."""
        return PuzzleGameOptionsFlow()


class PuzzleGameOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Puzzle Game."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        agents = await _get_conversation_agents(self.hass)
        current_agent = self.config_entry.data.get(CONF_CONVERSATION_AGENT, "default")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CONVERSATION_AGENT,
                        default=current_agent,
                    ): vol.In(agents),
                }
            ),
        )
