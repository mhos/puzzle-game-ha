"""Coordinator for Puzzle Game integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_CONVERSATION_AGENT
from .storage import PuzzleGameStorage
from .game_manager import GameManager
from .ai_client import generate_puzzle

_LOGGER = logging.getLogger(__name__)


class PuzzleGameCoordinator:
    """Coordinate game state between storage, services, and sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        storage: PuzzleGameStorage,
        conversation_agent: str | None = None,
    ) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.storage = storage
        self.game_manager = GameManager(storage)
        self.conversation_agent = conversation_agent
        self._sensor = None
        self._session_active = False
        self._active_satellite = None
        self._stt_unsub = None
        self._view_assist_device = None

    def register_sensor(self, sensor) -> None:
        """Register the sensor entity."""
        self._sensor = sensor

    @callback
    def _update_sensor(self, state_data: dict[str, Any]) -> None:
        """Update the sensor with new state."""
        if self._sensor:
            self._sensor.update_state(state_data)

    @property
    def session_active(self) -> bool:
        """Return whether a voice session is currently active."""
        return self._session_active

    @property
    def active_satellite(self) -> str | None:
        """Return the active satellite entity."""
        return self._active_satellite

    def set_session_active(self, active: bool, satellite: str | None = None, view_assist_device: str | None = None) -> None:
        """Set the voice session active state and optionally the satellite."""
        self._session_active = active
        if satellite is not None:
            self._active_satellite = satellite
            # Derive STT sensor from satellite name and start watching
            device_name = satellite.split('.')[1] if '.' in satellite else satellite
            stt_sensor = f"sensor.{device_name}_stt"
            self._start_stt_watch(stt_sensor)
        if view_assist_device is not None:
            self._view_assist_device = view_assist_device
        if not active:
            # Stop watching STT when session ends
            self._stop_stt_watch()
            self._active_satellite = None
            self._view_assist_device = None
        # Trigger a sensor update
        game = self.storage.get_current_game()
        if game:
            state_data = self.game_manager.get_game_state_dict(game)
        else:
            state_data = self._get_empty_state()
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

    def _start_stt_watch(self, stt_sensor: str) -> None:
        """Start watching the STT sensor for changes."""
        # Stop any existing watch first
        self._stop_stt_watch()

        @callback
        def _stt_state_changed(event: Event) -> None:
            """Handle STT sensor state change."""
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")

            if new_state is None:
                return

            new_value = new_state.state
            old_value = old_state.state if old_state else ""

            # Only fire event if there's actual speech content and it changed
            if new_value and len(new_value) > 0 and new_value != old_value:
                # Fire custom event for the blueprint to catch
                # Pass state values as simple strings for template access
                self.hass.bus.async_fire("puzzle_game_speech", {
                    "entity_id": stt_sensor,
                    "text": new_value,
                    "old_text": old_value,
                })
                _LOGGER.info("Fired puzzle_game_speech event: %s", new_value)

        self._stt_unsub = async_track_state_change_event(
            self.hass, [stt_sensor], _stt_state_changed
        )
        _LOGGER.info("Started watching STT sensor: %s", stt_sensor)

    def _stop_stt_watch(self) -> None:
        """Stop watching the STT sensor."""
        if self._stt_unsub:
            self._stt_unsub()
            self._stt_unsub = None
            _LOGGER.info("Stopped watching STT sensor")

    def _get_empty_state(self) -> dict[str, Any]:
        """Return empty game state."""
        return {
            "game_id": None,
            "phase": None,
            "word_number": None,
            "score": 0,
            "reveals": 0,
            "blanks": "",
            "clue": "",
            "solved_words": [],
            "solved_word_indices": [],
            "is_active": False,
            "last_message": None,
            "theme_revealed": None,
            "session_active": self._session_active,
            "active_satellite": self._active_satellite,
            "view_assist_device": self._view_assist_device,
        }

    async def async_refresh_state(self) -> None:
        """Refresh state from storage and update sensor."""
        game = self.storage.get_current_game()
        if game:
            state_data = self.game_manager.get_game_state_dict(game)
        else:
            state_data = self._get_empty_state()
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

    async def start_game(self, bonus: bool = False) -> dict[str, Any]:
        """Start a new game or continue existing one.

        Args:
            bonus: If True, start a bonus game instead of daily puzzle

        Returns:
            Dict with success status and message
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")

        if bonus:
            # Check for existing active bonus game
            existing_bonus = self.storage.get_active_bonus_game()
            if existing_bonus:
                # Resume existing bonus game
                state_data = self.game_manager.get_game_state_dict(existing_bonus)
                await self.storage.set_current_game(existing_bonus["id"])
                self._update_sensor(state_data)
                return {
                    "success": True,
                    "message": f"Continuing your bonus game. {state_data['clue']}",
                    "game_state": state_data
                }

            # Create new bonus puzzle
            puzzle = await generate_puzzle(self.hass, self.conversation_agent)
            bonus_date = f"bonus_{datetime.utcnow().isoformat()}"
            await self.storage.save_puzzle(bonus_date, puzzle, is_daily=False)

            # Create new bonus game
            game = await self.storage.create_game(bonus_date, puzzle, is_bonus=True)

            clues = puzzle.get("clues", [])
            words = puzzle.get("words", [])
            first_clue = clues[0] if clues else "Start playing"
            first_word_desc = GameManager._word_description(words[0]) if words else ""

            if not first_clue.endswith(('.', '!', '?')):
                first_clue = f"{first_clue}."

            message = f"Bonus round! First clue: {first_clue} {first_word_desc}."
            game["last_message"] = message
            await self.storage.update_game(game["id"], {"last_message": message})

            state_data = self.game_manager.get_game_state_dict(game)
            self._update_sensor(state_data)

            return {
                "success": True,
                "message": message,
                "game_state": state_data
            }

        # Daily puzzle flow
        # Check if already completed today's puzzle
        completed = self.storage.get_completed_daily_game(today)
        if completed:
            return {
                "success": False,
                "message": "You've already completed today's puzzle! Say 'play bonus game' for another round.",
                "game_state": None
            }

        # Check for existing active daily game
        existing = self.storage.get_active_daily_game(today)
        if existing:
            state_data = self.game_manager.get_game_state_dict(existing)
            await self.storage.set_current_game(existing["id"])
            self._update_sensor(state_data)
            return {
                "success": True,
                "message": f"Continuing today's puzzle. {state_data['clue']}",
                "game_state": state_data
            }

        # Get or create today's puzzle
        puzzle = self.storage.get_daily_puzzle(today)
        if not puzzle:
            puzzle = await generate_puzzle(self.hass, self.conversation_agent)
            await self.storage.save_puzzle(today, puzzle, is_daily=True)

        # Create new game
        game = await self.storage.create_game(today, puzzle, is_bonus=False)

        clues = puzzle.get("clues", [])
        words = puzzle.get("words", [])
        first_clue = clues[0] if clues else "Start playing"
        first_word_desc = GameManager._word_description(words[0]) if words else ""

        if not first_clue.endswith(('.', '!', '?')):
            first_clue = f"{first_clue}."

        message = f"New puzzle! First clue: {first_clue} {first_word_desc}."
        game["last_message"] = message
        await self.storage.update_game(game["id"], {"last_message": message})

        state_data = self.game_manager.get_game_state_dict(game)
        self._update_sensor(state_data)

        return {
            "success": True,
            "message": message,
            "game_state": state_data
        }

    async def submit_answer(self, answer: str) -> dict[str, Any]:
        """Submit an answer for the current game."""
        game = self.storage.get_current_game()
        if not game:
            return {
                "success": False,
                "message": "No active game. Say 'start puzzle game' to begin.",
                "game_state": None
            }

        if not game.get("is_active"):
            return {
                "success": False,
                "message": "Game is not active. Start a new game.",
                "game_state": None
            }

        result = await self.game_manager.submit_answer(game, answer)

        # Update last message
        game["last_message"] = result["message"]
        await self.storage.update_game(game["id"], {"last_message": result["message"]})

        # Refresh game from storage (it may have been updated)
        game = self.storage.get_game(game["id"])
        state_data = self.game_manager.get_game_state_dict(game)
        # Preserve session state
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

        return {
            "success": result["correct"],
            "message": result["message"],
            "game_state": state_data
        }

    async def reveal_letter(self) -> dict[str, Any]:
        """Reveal a letter in the current word."""
        game = self.storage.get_current_game()
        if not game:
            return {
                "success": False,
                "message": "No active game.",
                "game_state": None
            }

        if not game.get("is_active"):
            return {
                "success": False,
                "message": "Game is not active.",
                "game_state": None
            }

        result = await self.game_manager.reveal_letter(game)

        game["last_message"] = result["message"]
        await self.storage.update_game(game["id"], {"last_message": result["message"]})

        game = self.storage.get_game(game["id"])
        state_data = self.game_manager.get_game_state_dict(game)
        # Preserve session state
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

        return {
            "success": result["success"],
            "message": result["message"],
            "game_state": state_data
        }

    async def skip_word(self) -> dict[str, Any]:
        """Skip the current word."""
        game = self.storage.get_current_game()
        if not game:
            return {
                "success": False,
                "message": "No active game.",
                "game_state": None
            }

        if not game.get("is_active"):
            return {
                "success": False,
                "message": "Game is not active.",
                "game_state": None
            }

        result = await self.game_manager.skip_word(game)

        game["last_message"] = result["message"]
        await self.storage.update_game(game["id"], {"last_message": result["message"]})

        game = self.storage.get_game(game["id"])
        state_data = self.game_manager.get_game_state_dict(game)
        # Preserve session state
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

        return {
            "success": result["success"],
            "message": result["message"],
            "game_state": state_data
        }

    async def repeat_clue(self) -> dict[str, Any]:
        """Repeat the current clue."""
        game = self.storage.get_current_game()
        if not game:
            return {
                "success": False,
                "message": "No active game.",
                "game_state": None
            }

        clue = self.game_manager.get_current_clue(game)

        game["last_message"] = clue
        await self.storage.update_game(game["id"], {"last_message": clue})

        state_data = self.game_manager.get_game_state_dict(game)
        # Preserve session state
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

        return {
            "success": True,
            "message": clue,
            "game_state": state_data
        }

    async def spell_word(self) -> dict[str, Any]:
        """Spell out the current word letter by letter."""
        game = self.storage.get_current_game()
        if not game:
            return {
                "success": False,
                "message": "No active game.",
                "game_state": None
            }

        puzzle = game.get("puzzle", {})
        words = puzzle.get("words", [])
        current_index = game.get("current_word_index", 0)

        if current_index < len(words):
            word = words[current_index]
            # Spell it out with pauses: "C. A. T."
            spelled = ". ".join(letter.upper() for letter in word) + "."
            message = f"The word is spelled: {spelled}"
        else:
            message = "No word to spell."

        game["last_message"] = message
        await self.storage.update_game(game["id"], {"last_message": message})

        state_data = self.game_manager.get_game_state_dict(game)
        # Preserve session state
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

        return {
            "success": True,
            "message": message,
            "game_state": state_data
        }

    async def give_up(self) -> dict[str, Any]:
        """Give up and end the game."""
        game = self.storage.get_current_game()
        if not game:
            return {
                "success": False,
                "message": "No active game.",
                "game_state": None
            }

        result = await self.game_manager.give_up(game)

        game["last_message"] = result["message"]
        await self.storage.update_game(game["id"], {"last_message": result["message"]})

        game = self.storage.get_game(game["id"])
        state_data = self.game_manager.get_game_state_dict(game)
        # Preserve session state
        state_data["session_active"] = self._session_active
        state_data["active_satellite"] = self._active_satellite
        state_data["view_assist_device"] = self._view_assist_device
        self._update_sensor(state_data)

        return {
            "success": True,
            "message": result["message"],
            "game_state": state_data
        }
