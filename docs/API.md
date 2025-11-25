# Puzzle Game API Documentation

Base URL: `http://YOUR_HOST:5000`

## Endpoints

### Health Check

#### GET `/`
Check if the server is running.

**Response:**
```json
{
  "status": "ok",
  "service": "Puzzle Game API"
}
```

---

### Start Game

#### POST `/api/game/start`
Start a new game or continue an existing one.

**Request Body:**
```json
{
  "user_id": "optional_user_id",
  "bonus": false
}
```

**Parameters:**
- `user_id` (optional): User identifier
- `bonus` (boolean): `true` for bonus game, `false` for daily puzzle

**Response:**
```json
{
  "success": true,
  "message": "First clue: [clue text]. Word has [X] letters.",
  "game_state": {
    "game_id": "uuid",
    "phase": 1,
    "word_number": 1,
    "score": 0,
    "reveals": 0,
    "blanks": "_ _ _ _ _",
    "clue": "Clue text",
    "solved_words": [],
    "solved_word_indices": [],
    "is_active": true
  }
}
```

**Behavior:**
- Daily puzzles: Returns existing game if active, or creates new one for today
- Bonus games: Returns existing active bonus game, or creates new one
- Only one active daily game and one active bonus game allowed at a time

---

### Get Latest Game

#### GET `/api/game/latest`
Get the ID of the most recent active game.

**Response:**
```json
{
  "game_id": "uuid"
}
```

---

### Get Game State

#### GET `/api/game/{game_id}`
Get the current state of a game.

**Path Parameters:**
- `game_id`: UUID of the game

**Response:**
```json
{
  "game_id": "uuid",
  "phase": 1,
  "word_number": 1,
  "score": 10,
  "reveals": 1,
  "blanks": "_ _ R _ _",
  "clue": "Current clue text",
  "solved_words": ["WORD1"],
  "solved_word_indices": [0],
  "is_active": true,
  "theme_revealed": null,
  "last_message": "Correct! Moving to next word."
}
```

**Phase Values:**
- `1`: Solving individual words
- `2`: Final answer (guessing the theme)

---

### Submit Answer

#### POST `/api/game/{game_id}/answer`
Submit an answer for the current word or theme.

**Path Parameters:**
- `game_id`: UUID of the game

**Request Body:**
```json
{
  "answer": "FLYING"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Correct! +10 points. Moving to word 2.",
  "game_state": { ... }
}
```

**Answer Matching:**
- Case-insensitive
- Spaces removed for comparison (multi-word answers supported)
- Must match revealed letters if any

**Score Changes:**
- Correct answer in Phase 1: +10 points, +1 reveal
- Correct theme in Phase 2: +20 points
- Wrong answer: No score change

---

### Reveal Letter

#### POST `/api/game/{game_id}/reveal`
Reveal a random letter in the current word.

**Path Parameters:**
- `game_id`: UUID of the game

**Response:**
```json
{
  "success": true,
  "message": "Here's a letter: F _ _ G _ T. 0 reveals left.",
  "game_state": { ... }
}
```

**Rules:**
- Costs 1 reveal
- Reveals random unrevealed letter
- Phase 2 (final answer): Only ONE manual reveal allowed
- Returns error if no reveals left or all letters already revealed

---

### Skip Word

#### POST `/api/game/{game_id}/skip`
Skip the current word and move to the next unsolved word.

**Path Parameters:**
- `game_id`: UUID of the game

**Response:**
```json
{
  "success": true,
  "message": "[Next clue text]",
  "game_state": { ... }
}
```

**Rules:**
- Only available in Phase 1
- Skipped words are returned to after all non-skipped words attempted
- Returns error if called during Phase 2

---

### Repeat Clue

#### POST `/api/game/{game_id}/repeat`
Repeat the current clue.

**Path Parameters:**
- `game_id`: UUID of the game

**Response:**
```json
{
  "success": true,
  "message": "[Current clue text]",
  "game_state": { ... }
}
```

---

### Give Up

#### POST `/api/game/{game_id}/giveup`
End the game and reveal all answers.

**Path Parameters:**
- `game_id`: UUID of the game

**Response:**
```json
{
  "success": true,
  "message": "Game over. Final score: [X]. The answers were: [words]. The theme was: [theme].",
  "game_state": {
    "is_active": false,
    ...
  }
}
```

---

## Game State Object

The game state object is returned by most endpoints:

```json
{
  "game_id": "string (UUID)",
  "phase": "integer (1 or 2)",
  "word_number": "integer (1-5)",
  "score": "integer",
  "reveals": "integer",
  "blanks": "string (current word with blanks)",
  "clue": "string (current clue text)",
  "solved_words": ["array of solved words"],
  "solved_word_indices": ["array of indices (0-4)"],
  "is_active": "boolean",
  "theme_revealed": "string or null",
  "last_message": "string (last game message)"
}
```

## Error Responses

All endpoints may return error responses:

```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request
- `404`: Game not found
- `500`: Server error

## Example Usage

### Starting a Daily Game

```bash
curl -X POST http://localhost:5000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"bonus": false}'
```

### Submitting an Answer

```bash
curl -X POST http://localhost:5000/api/game/{game_id}/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "FLYING"}'
```

### Getting Game State

```bash
curl http://localhost:5000/api/game/{game_id}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider adding this if deploying publicly.

## Authentication

Currently no authentication is required. The `user_id` parameter is optional and for tracking purposes only.
