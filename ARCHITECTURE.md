# Native Home Assistant Integration Architecture

## Overview

This document outlines the conversion of the Puzzle Game from a FastAPI server + HA automations to a **native Home Assistant custom integration** that works on all HA installation types.

## Current Architecture (FastAPI)

```
┌─────────────────────┐     REST API      ┌─────────────────────┐
│  Home Assistant     │ ───────────────>  │  FastAPI Server     │
│  - Automations      │                   │  - Game Logic       │
│  - REST Commands    │ <───────────────  │  - SQLite DB        │
│  - REST Sensors     │                   │  - Static Files     │
└─────────────────────┘                   └─────────────────────┘
```

## New Architecture (Native Integration)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Home Assistant                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              puzzle_game Integration                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   Services   │  │   Sensors    │  │   Storage    │   │   │
│  │  │  start_game  │  │ game_state   │  │  .storage/   │   │   │
│  │  │  answer      │  │              │  │  puzzle_game │   │   │
│  │  │  reveal      │  │              │  │              │   │   │
│  │  │  skip        │  │              │  │              │   │   │
│  │  │  give_up     │  │              │  │              │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────────────────────────┐ │   │
│  │  │  AI Client   │  │        Game Manager              │ │   │
│  │  │ (HA Convo)   │  │   (Pure Python game logic)       │ │   │
│  │  └──────────────┘  └──────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────────────────────┐   │
│  │  www/ folder    │     │  Automations/Blueprint          │   │
│  │  - dashboard    │     │  - Voice triggers               │   │
│  │  - sounds       │     │  - Call services                │   │
│  └─────────────────┘     └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

```
custom_components/
└── puzzle_game/
    ├── __init__.py           # Integration setup, services registration
    ├── manifest.json         # Integration metadata
    ├── const.py              # Constants (points, max score, etc.)
    ├── game_manager.py       # Core game logic (adapted from game_logic.py)
    ├── ai_client.py          # Puzzle generation via HA conversation agent
    ├── storage.py            # Persistent storage using HA's .storage
    ├── sensor.py             # Game state sensor entity
    ├── services.yaml         # Service definitions
    ├── config_flow.py        # UI configuration (optional)
    ├── strings.json          # Localization
    └── translations/
        └── en.json           # English translations

www/
└── puzzle_game/
    ├── dashboard.html        # Game dashboard (modified for HA API)
    ├── wrong.mp3             # Wrong answer sound
    └── startgame.mp3         # Game start music
```

## Services

Replace REST API endpoints with HA services:

| Old REST Endpoint | New HA Service | Parameters |
|-------------------|----------------|------------|
| POST /api/game/start | `puzzle_game.start_game` | `bonus: bool` |
| POST /api/game/{id}/answer | `puzzle_game.submit_answer` | `answer: str` |
| POST /api/game/{id}/reveal | `puzzle_game.reveal_letter` | (none) |
| POST /api/game/{id}/skip | `puzzle_game.skip_word` | (none) |
| POST /api/game/{id}/repeat | `puzzle_game.repeat_clue` | (none) |
| POST /api/game/{id}/giveup | `puzzle_game.give_up` | (none) |

## Sensor

`sensor.puzzle_game` with attributes:
- `game_id`: Current game ID
- `phase`: 1 (words) or 2 (final answer)
- `word_number`: Current word (1-5) or 6 for final
- `score`: Current score
- `reveals`: Available reveals
- `blanks`: Current word with blanks (e.g., "_ O G")
- `clue`: Current clue text
- `solved_words`: List of solved words
- `solved_word_indices`: Indices of solved words
- `is_active`: Whether game is in progress
- `last_message`: Last feedback message (for TTS)
- `theme_revealed`: Final theme (when game ends)

State value: Current clue or "No active game"

## Storage

Use HA's built-in storage system (`.storage/puzzle_game`):

```json
{
  "version": 1,
  "data": {
    "puzzles": {
      "2024-12-03": {
        "theme": "BASEBALL",
        "words": ["PITCHER", "STRIKE", "DIAMOND", "GLOVE", "HOMERUN"],
        "clues": ["Player who throws...", ...],
        "is_daily": true
      }
    },
    "games": {
      "uuid-1234": {
        "puzzle_date": "2024-12-03",
        "phase": 1,
        "current_word_index": 2,
        "score": 20,
        "reveals": 2,
        "solved_words": [0, 1],
        "skipped_words": [],
        "revealed_letters": {"0": [1, 3]},
        "is_active": true,
        "started_at": "2024-12-03T10:00:00Z"
      }
    },
    "current_game_id": "uuid-1234"
  }
}
```

## AI Integration

Replace Ollama with HA's conversation agent:

```python
async def generate_puzzle(hass):
    """Generate puzzle using HA's conversation agent."""
    prompt = """Generate a word puzzle with:
    THEME: [single word or phrase]
    WORD1: [word] | [clue]
    WORD2: [word] | [clue]
    ...
    """

    # Call HA conversation service
    response = await hass.services.async_call(
        "conversation",
        "process",
        {"text": prompt},
        blocking=True,
        return_response=True
    )

    # Parse response into puzzle format
    return parse_puzzle_response(response)
```

User can configure which conversation agent to use in the integration config.

## Dashboard Changes

The dashboard needs to poll HA's REST API instead of FastAPI:

```javascript
// Old
const API_BASE = 'http://192.168.1.100:5000';
const response = await fetch(`${API_BASE}/api/game/${gameId}`);

// New - use HA's REST API
const API_BASE = '';  // Same origin
const response = await fetch(`/api/states/sensor.puzzle_game`, {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('hassToken')}`,
        'Content-Type': 'application/json'
    }
});
```

Or better: Use a WebSocket connection to subscribe to state changes.

## Installation Flow

### For Users (via HACS):

1. Add custom repository to HACS
2. Install "Puzzle Game" integration
3. Restart Home Assistant
4. Go to Settings > Integrations > Add Integration > Puzzle Game
5. Select conversation agent for puzzle generation
6. Dashboard files auto-copied to www/puzzle_game/
7. Import blueprint for voice commands

### For Users (Manual):

1. Copy `custom_components/puzzle_game` to config folder
2. Copy `www/puzzle_game` to config folder
3. Restart Home Assistant
4. Add integration via UI
5. Import blueprint

## Blueprint Changes

The blueprint changes from REST commands to service calls:

```yaml
# Old
- service: rest_command.puzzle_start_game

# New
- service: puzzle_game.start_game
  data:
    bonus: false
```

Response data comes from sensor attributes instead of REST response.

## Advantages of Native Integration

1. **Works on ALL HA installations** - HAOS, Container, Core, Supervised
2. **No separate server** - Everything runs inside HA
3. **Proper HA integration** - Shows in integrations list, proper entities
4. **HACS installable** - One-click install for most users
5. **Uses HA's AI** - Works with any conversation agent user has configured
6. **Persistent storage** - Uses HA's storage system, survives restarts
7. **Proper state management** - Real entities with history, automations, etc.

## Migration Path

1. Create new integration structure
2. Port game_logic.py to game_manager.py (mostly same logic)
3. Replace SQLite with HA storage
4. Replace Ollama with conversation agent
5. Create sensor entity
6. Register services
7. Update dashboard for HA API
8. Update blueprint to use services
9. Create HACS repository structure
10. Update documentation
