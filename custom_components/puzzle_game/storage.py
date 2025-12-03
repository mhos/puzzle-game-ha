"""Storage management for Puzzle Game."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


class PuzzleGameStorage:
    """Handle storage for puzzle game data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize storage."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from storage."""
        data = await self._store.async_load()
        if data is None:
            self._data = {
                "puzzles": {},
                "games": {},
                "current_game_id": None,
            }
        else:
            self._data = data

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    # Puzzle methods
    def get_daily_puzzle(self, date: str) -> dict | None:
        """Get puzzle for a specific date."""
        return self._data.get("puzzles", {}).get(date)

    async def save_puzzle(self, date: str, puzzle: dict, is_daily: bool = True) -> None:
        """Save a puzzle."""
        if "puzzles" not in self._data:
            self._data["puzzles"] = {}

        puzzle_data = {
            **puzzle,
            "is_daily": is_daily,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._data["puzzles"][date] = puzzle_data
        await self.async_save()

    # Game methods
    def get_game(self, game_id: str) -> dict | None:
        """Get a game by ID."""
        return self._data.get("games", {}).get(game_id)

    def get_current_game_id(self) -> str | None:
        """Get current active game ID."""
        return self._data.get("current_game_id")

    def get_current_game(self) -> dict | None:
        """Get the current active game."""
        game_id = self.get_current_game_id()
        if game_id:
            return self.get_game(game_id)
        return None

    async def create_game(self, puzzle_date: str, puzzle: dict, is_bonus: bool = False) -> dict:
        """Create a new game."""
        if "games" not in self._data:
            self._data["games"] = {}

        game_id = str(uuid.uuid4())
        game = {
            "id": game_id,
            "puzzle_date": puzzle_date,
            "puzzle": puzzle,  # Store puzzle data with game
            "is_bonus": is_bonus,
            "phase": 1,
            "current_word_index": 0,
            "score": 0,
            "reveals": 0,
            "solved_words": [],
            "skipped_words": [],
            "revealed_letters": {},
            "is_active": True,
            "gave_up": False,
            "last_message": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }

        self._data["games"][game_id] = game
        self._data["current_game_id"] = game_id
        await self.async_save()

        return game

    async def update_game(self, game_id: str, updates: dict) -> dict | None:
        """Update a game."""
        if game_id not in self._data.get("games", {}):
            return None

        self._data["games"][game_id].update(updates)
        await self.async_save()

        return self._data["games"][game_id]

    async def set_current_game(self, game_id: str | None) -> None:
        """Set the current active game."""
        self._data["current_game_id"] = game_id
        await self.async_save()

    def get_active_daily_game(self, date: str) -> dict | None:
        """Get active game for today's daily puzzle."""
        for game_id, game in self._data.get("games", {}).items():
            if (game.get("puzzle_date") == date and
                game.get("is_active") and
                not game.get("is_bonus")):
                return game
        return None

    def get_completed_daily_game(self, date: str) -> dict | None:
        """Get completed game for today's daily puzzle."""
        for game_id, game in self._data.get("games", {}).items():
            if (game.get("puzzle_date") == date and
                not game.get("is_active") and
                not game.get("is_bonus") and
                game.get("completed_at")):
                return game
        return None

    def get_active_bonus_game(self) -> dict | None:
        """Get any active bonus game."""
        for game_id, game in self._data.get("games", {}).items():
            if game.get("is_bonus") and game.get("is_active"):
                return game
        return None

    async def cleanup_old_games(self, days_to_keep: int = 7) -> None:
        """Remove games older than specified days."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        games_to_remove = []

        for game_id, game in self._data.get("games", {}).items():
            started_at = game.get("started_at")
            if started_at:
                try:
                    game_date = datetime.fromisoformat(started_at)
                    if game_date < cutoff and not game.get("is_active"):
                        games_to_remove.append(game_id)
                except ValueError:
                    pass

        for game_id in games_to_remove:
            del self._data["games"][game_id]

        if games_to_remove:
            await self.async_save()
            _LOGGER.debug("Cleaned up %d old games", len(games_to_remove))
