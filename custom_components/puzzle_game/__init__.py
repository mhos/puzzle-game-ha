"""The Puzzle Game integration."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
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
    SERVICE_SET_SESSION,
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

SERVICE_SET_SESSION_SCHEMA = vol.Schema(
    {
        vol.Required("active"): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Puzzle Game from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Auto-copy www files to config/www/puzzle_game/
    await _async_setup_frontend(hass)

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


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Copy frontend files to www directory and clean up old files."""
    # Source: custom_components/puzzle_game/www/
    source_dir = Path(__file__).parent / "www"

    # Destination: config/www/community/puzzle_game/
    dest_dir = Path(hass.config.path("www")) / "community" / "puzzle_game"

    # Files that should no longer exist (old/deprecated files)
    deprecated_files = [
        "dashboard.html",
        "wrong.mp3",
        "startup.mp3",
    ]

    def copy_and_cleanup():
        """Copy files and remove deprecated ones (runs in executor)."""
        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Remove deprecated files
        for old_file in deprecated_files:
            old_path = dest_dir / old_file
            if old_path.exists():
                old_path.unlink()
                _LOGGER.info("Removed deprecated file: %s", old_file)

        # Get list of current source files
        source_files = {f.name for f in source_dir.iterdir() if f.is_file()}

        # Remove any files in dest that are not in source (cleanup orphans)
        if dest_dir.exists():
            for dest_file in dest_dir.iterdir():
                if dest_file.is_file() and dest_file.name not in source_files:
                    dest_file.unlink()
                    _LOGGER.info("Removed orphaned file: %s", dest_file.name)

        # Copy each file from source
        for source_file in source_dir.iterdir():
            if source_file.is_file():
                dest_file = dest_dir / source_file.name
                # Only copy if source is newer or dest doesn't exist
                if not dest_file.exists() or source_file.stat().st_mtime > dest_file.stat().st_mtime:
                    shutil.copy2(source_file, dest_file)
                    _LOGGER.debug("Copied %s to %s", source_file.name, dest_file)

    try:
        await hass.async_add_executor_job(copy_and_cleanup)
        _LOGGER.info("Puzzle Game frontend files installed to %s", dest_dir)
    except Exception as err:
        _LOGGER.warning("Could not copy frontend files: %s", err)


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
        coordinator.set_session_active(active)
        return {
            "success": True,
            "session_active": active,
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SESSION,
        handle_set_session,
        schema=SERVICE_SET_SESSION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
