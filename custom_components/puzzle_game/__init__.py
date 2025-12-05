"""The Puzzle Game integration."""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
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
    SERVICE_SPELL_WORD,
    SERVICE_GIVE_UP,
    SERVICE_SET_SESSION,
)
from .storage import PuzzleGameStorage
from .coordinator import PuzzleGameCoordinator

_LOGGER = logging.getLogger(__name__)

# Panel version - increment when frontend changes
PANEL_VERSION = "1.0.7"
PANEL_URL = "puzzle-game"
PANEL_TITLE = "Puzzle Game"
PANEL_ICON = "mdi:owl"

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

SERVICE_SET_SESSION_SCHEMA = vol.Schema(
    {
        vol.Required("active"): cv.boolean,
        vol.Optional("satellite"): cv.entity_id,
        vol.Optional("view_assist_device"): cv.entity_id,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Puzzle Game from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Register the panel (sidebar entry) and serve frontend files
    await _async_register_panel(hass)

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


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the Puzzle Game panel in the sidebar."""
    _LOGGER.info("Starting panel registration for Puzzle Game")

    # Path to frontend files
    frontend_path = Path(__file__).parent / "frontend"
    panel_js_path = frontend_path / "panel.js"

    _LOGGER.info("Looking for panel.js at: %s", panel_js_path)

    if not panel_js_path.exists():
        _LOGGER.error("Panel JS file not found at %s", panel_js_path)
        return

    _LOGGER.info("Panel JS file found, registering static path")

    # Register static path for the panel JS file
    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    f"/puzzle_game/panel-{PANEL_VERSION}.js",
                    str(panel_js_path),
                    False,  # Disable cache for development
                )
            ]
        )
        _LOGGER.info("Static path registered: /puzzle_game/panel-%s.js", PANEL_VERSION)
    except RuntimeError as err:
        # Static path may already be registered from a previous load
        if "already registered" in str(err).lower():
            _LOGGER.info("Static path already registered, continuing")
        else:
            _LOGGER.error("Failed to register static path: %s", err)
            return
    except Exception as err:
        _LOGGER.error("Failed to register static path: %s", err)
        return

    _LOGGER.info("Registering panel with panel_custom.async_register_panel")

    # Register the panel using panel_custom
    try:
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name="puzzle-game-panel",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=f"/puzzle_game/panel-{PANEL_VERSION}.js",
            embed_iframe=False,
            trust_external=False,
            require_admin=False,
        )
        _LOGGER.info("Puzzle Game panel successfully registered at /%s", PANEL_URL)
    except Exception as err:
        _LOGGER.error("Failed to register panel: %s (type: %s)", err, type(err).__name__)

    # Clean up old www files from previous versions
    await _async_cleanup_old_files(hass)


async def _async_cleanup_old_files(hass: HomeAssistant) -> None:
    """Remove old www files from previous versions."""
    # Old destination from previous versions
    old_www_dir = Path(hass.config.path("www")) / "community" / "puzzle_game"

    def cleanup():
        """Remove old files (runs in executor)."""
        if old_www_dir.exists():
            try:
                shutil.rmtree(old_www_dir)
                _LOGGER.info("Removed old www files from %s", old_www_dir)
            except Exception as err:
                _LOGGER.debug("Could not remove old www files: %s", err)

    try:
        await hass.async_add_executor_job(cleanup)
    except Exception as err:
        _LOGGER.debug("Cleanup failed: %s", err)


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
            SERVICE_SET_SESSION,
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

    async def handle_spell_word(call: ServiceCall) -> ServiceResponse:
        """Handle spell word service."""
        result = await coordinator.spell_word()
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

    async def handle_set_session(call: ServiceCall) -> ServiceResponse:
        """Handle set session service."""
        active = call.data.get("active", False)
        satellite = call.data.get("satellite")
        view_assist_device = call.data.get("view_assist_device")
        coordinator.set_session_active(active, satellite, view_assist_device)
        return {
            "success": True,
            "session_active": active,
            "active_satellite": satellite,
            "view_assist_device": view_assist_device,
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
        SERVICE_SPELL_WORD,
        handle_spell_word,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GIVE_UP,
        handle_give_up,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SESSION,
        handle_set_session,
        schema=SERVICE_SET_SESSION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
