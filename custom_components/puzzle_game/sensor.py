"""Sensor platform for Puzzle Game."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SENSOR_NAME,
    ATTR_GAME_ID,
    ATTR_PHASE,
    ATTR_WORD_NUMBER,
    ATTR_SCORE,
    ATTR_REVEALS,
    ATTR_BLANKS,
    ATTR_CLUE,
    ATTR_SOLVED_WORDS,
    ATTR_SOLVED_WORD_INDICES,
    ATTR_IS_ACTIVE,
    ATTR_LAST_MESSAGE,
    ATTR_THEME_REVEALED,
    ATTR_SESSION_ACTIVE,
    ATTR_ACTIVE_SATELLITE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Puzzle Game sensor."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([PuzzleGameSensor(coordinator, config_entry)])


class PuzzleGameSensor(SensorEntity):
    """Sensor representing the current puzzle game state."""

    _attr_has_entity_name = True
    _attr_name = None  # Use device name

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_game_state"
        self._state_data: dict[str, Any] = {}

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": SENSOR_NAME,
            "manufacturer": "Puzzle Game",
            "model": "Voice Puzzle Game",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self) -> str:
        """Return the current clue or status."""
        if not self._state_data.get(ATTR_IS_ACTIVE):
            if self._state_data.get(ATTR_GAME_ID):
                return "Game completed"
            return "No active game"
        return self._state_data.get(ATTR_CLUE, "No active game")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all game state attributes."""
        return {
            ATTR_GAME_ID: self._state_data.get(ATTR_GAME_ID),
            ATTR_PHASE: self._state_data.get(ATTR_PHASE),
            ATTR_WORD_NUMBER: self._state_data.get(ATTR_WORD_NUMBER),
            ATTR_SCORE: self._state_data.get(ATTR_SCORE, 0),
            ATTR_REVEALS: self._state_data.get(ATTR_REVEALS, 0),
            ATTR_BLANKS: self._state_data.get(ATTR_BLANKS, ""),
            ATTR_CLUE: self._state_data.get(ATTR_CLUE, ""),
            ATTR_SOLVED_WORDS: self._state_data.get(ATTR_SOLVED_WORDS, []),
            ATTR_SOLVED_WORD_INDICES: self._state_data.get(ATTR_SOLVED_WORD_INDICES, []),
            ATTR_IS_ACTIVE: self._state_data.get(ATTR_IS_ACTIVE, False),
            ATTR_LAST_MESSAGE: self._state_data.get(ATTR_LAST_MESSAGE),
            ATTR_THEME_REVEALED: self._state_data.get(ATTR_THEME_REVEALED),
            ATTR_SESSION_ACTIVE: self._state_data.get(ATTR_SESSION_ACTIVE, False),
            ATTR_ACTIVE_SATELLITE: self._state_data.get(ATTR_ACTIVE_SATELLITE),
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._state_data.get(ATTR_IS_ACTIVE):
            return "mdi:puzzle"
        return "mdi:puzzle-outline"

    @callback
    def update_state(self, state_data: dict[str, Any]) -> None:
        """Update the sensor state."""
        self._state_data = state_data
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        # Register with coordinator
        self.coordinator.register_sensor(self)

        # Load initial state
        await self.coordinator.async_refresh_state()
