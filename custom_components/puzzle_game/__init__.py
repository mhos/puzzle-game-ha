"""The Puzzle Game integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_CONVERSATION_AGENT,
    SERVICE_START_GAME,
    SERVICE_SUBMIT_ANSWER,
    SERVICE_REVEAL_LETTER,
    SERVICE_SKIP_WORD,
    SERVICE_REPEAT_CLUE,
    SERVICE_GIVE_UP,
)
from .storage import PuzzleGameStorage
from .coordinator import PuzzleGameCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Service schemas
SERVICE_START_GAME_SCHEMA = vol.Schema(
    {
        vol.Optional("bonus", default=False): cv.boolean,
    }
)

SERVICE_SUBMIT_ANSWER_SCHEMA = vol.Schema(
    {
        vol.Required("answer"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Puzzle Game from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize storage
    storage = PuzzleGameStorage(hass)
    await storage.async_load()

    # Get conversation agent from config
    conversation_agent = entry.data.get(CONF_CONVERSATION_AGENT)
    if conversation_agent == "default":
        conversation_agent = None

    # Create coordinator
    coordinator = PuzzleGameCoordinator(hass, storage, conversation_agent)

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "storage": storage,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_setup_services(hass, coordinator)

    # Clean up old games
    await storage.cleanup_old_games()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    # Remove services if no more entries
    if not hass.data[DOMAIN]:
        for service in [
            SERVICE_START_GAME,
            SERVICE_SUBMIT_ANSWER,
            SERVICE_REVEAL_LETTER,
            SERVICE_SKIP_WORD,
            SERVICE_REPEAT_CLUE,
            SERVICE_GIVE_UP,
        ]:
            hass.services.async_remove(DOMAIN, service)

    return unload_ok


async def _async_setup_services(hass: HomeAssistant, coordinator: PuzzleGameCoordinator) -> None:
    """Set up services for Puzzle Game."""

    async def handle_start_game(call: ServiceCall) -> ServiceResponse:
        """Handle start game service."""
        bonus = call.data.get("bonus", False)
        result = await coordinator.start_game(bonus=bonus)
        return {
            "success": result["success"],
            "message": result["message"],
        }

    async def handle_submit_answer(call: ServiceCall) -> ServiceResponse:
        """Handle submit answer service."""
        answer = call.data.get("answer", "")
        result = await coordinator.submit_answer(answer)
        return {
            "success": result["success"],
            "message": result["message"],
        }

    async def handle_reveal_letter(call: ServiceCall) -> ServiceResponse:
        """Handle reveal letter service."""
        result = await coordinator.reveal_letter()
        return {
            "success": result["success"],
            "message": result["message"],
        }

    async def handle_skip_word(call: ServiceCall) -> ServiceResponse:
        """Handle skip word service."""
        result = await coordinator.skip_word()
        return {
            "success": result["success"],
            "message": result["message"],
        }

    async def handle_repeat_clue(call: ServiceCall) -> ServiceResponse:
        """Handle repeat clue service."""
        result = await coordinator.repeat_clue()
        return {
            "success": result["success"],
            "message": result["message"],
        }

    async def handle_give_up(call: ServiceCall) -> ServiceResponse:
        """Handle give up service."""
        result = await coordinator.give_up()
        return {
            "success": result["success"],
            "message": result["message"],
        }

    # Register services with response support
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_GAME,
        handle_start_game,
        schema=SERVICE_START_GAME_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SUBMIT_ANSWER,
        handle_submit_answer,
        schema=SERVICE_SUBMIT_ANSWER_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REVEAL_LETTER,
        handle_reveal_letter,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SKIP_WORD,
        handle_skip_word,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REPEAT_CLUE,
        handle_repeat_clue,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GIVE_UP,
        handle_give_up,
        supports_response=SupportsResponse.OPTIONAL,
    )
