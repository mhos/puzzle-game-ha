# Puzzle Game for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&logo=homeassistant&logoColor=white)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mhos&repository=puzzle-game-ha&category=integration)

A voice-controlled word puzzle game that runs **natively in Home Assistant**. Works with [View Assist](https://dinki.github.io/View-Assist/) for visual display. Solve themed word puzzles completely hands-free!

## Features

- **Native HA Integration** - Runs inside Home Assistant, no separate server needed
- **Works Everywhere** - HAOS, Container, Core, Supervised - all installation types
- **Any AI Provider** - Uses your configured HA conversation agent (OpenAI, Google AI, Ollama, etc.)
- **Daily Puzzles** - Fresh AI-generated puzzle every day
- **Unlimited Bonus Rounds** - Play as many bonus games as you want
- **Voice Control** - Completely hands-free gameplay
- **Continuous Conversation** - No wake word needed during gameplay!
- **Auto-registering Panel** - Appears in sidebar automatically, no dashboard setup needed
- **Persistent State** - Resume games anytime

## How It Works

Each puzzle consists of 5 themed words plus a final "connection" answer:
1. Solve 5 word clues (10 points each)
2. Earn letter reveals for correct answers
3. Use reveals to get hints when stuck
4. Skip difficult words and return to them later
5. Guess the theme that connects all 5 words (20 point bonus)

---

## Installation (3 Easy Steps!)

### Prerequisites

- **Home Assistant 2024.1.0 or newer**
- **A conversation agent configured** (OpenAI, Google AI, Ollama, or any HA-compatible AI)
- **View Assist** (for visual dashboard and voice control)

### Step 1: Install via HACS

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=mhos&repository=puzzle-game-ha&category=integration" target="_blank"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

Click the button above, or manually:

1. Open HACS in Home Assistant
2. Click the three dots menu > **Custom repositories**
3. Add: `https://github.com/mhos/puzzle-game-ha`
4. Category: **Integration**
5. Click **Add**
6. Find "Puzzle Game" and click **Download**
7. Restart Home Assistant

### Step 2: Add the Integration

1. Go to **Settings > Devices & Services**
2. Click **Add Integration**
3. Search for "Puzzle Game"
4. Select which AI conversation agent to use for puzzle generation
5. Click **Submit**

> **Note:** A "Puzzle Game" entry will automatically appear in your sidebar!

### Step 3: Import the Blueprint

<a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fmhos%2Fpuzzle-game-ha%2Fblob%2Fmain%2Fhomeassistant%2Fblueprints%2Fautomation%2Fpuzzle_game_controller.yaml" target="_blank"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a>

Click the button above, or manually:

1. Go to **Settings > Automations & Scenes > Blueprints**
2. Click **Import Blueprint**
3. Paste: `https://github.com/mhos/puzzle-game-ha/blob/main/homeassistant/blueprints/automation/puzzle_game_controller.yaml`
4. Click **Preview** then **Import**
5. Click **Create Automation** from the blueprint

**That's it! You're ready to play!**

---

## Playing the Game

### Starting a Game

Say to your View Assist device:
- **"Start puzzle game"** - Begin a new daily puzzle
- **"Play bonus game"** - Start a bonus round
- **"Continue puzzle game"** - Resume a paused game

### During Gameplay (No Wake Word Needed!)

Once the game starts, speak directly without the wake word:

| Command | Action |
|---------|--------|
| Say the word directly | Submit your answer |
| "Spell" | Enter spelling mode |
| "Reveal" | Get a letter hint |
| "Skip" | Skip current word |
| "Repeat" | Hear the clue again |
| "Pause" | Pause the game |
| "Give up" | End the game |

### Spelling Mode

Say "spell" to enter spelling mode:
1. Say each letter one at a time
2. Say "done" when finished
3. The system will submit your spelled word

---

## Services

The integration provides these services:

| Service | Description |
|---------|-------------|
| `puzzle_game.start_game` | Start a new game (set `bonus: true` for bonus round) |
| `puzzle_game.submit_answer` | Submit an answer |
| `puzzle_game.reveal_letter` | Reveal a letter |
| `puzzle_game.skip_word` | Skip current word |
| `puzzle_game.repeat_clue` | Repeat the clue |
| `puzzle_game.give_up` | End the game |

## Sensor

`sensor.puzzle_game` provides:
- Current game state
- Score, reveals, phase
- Current clue and blanks
- Solved words
- Last feedback message

---

## Configuration

### Conversation Agent

During setup, you select which conversation agent generates puzzles. You can change this later in the integration options.

Supported agents:
- OpenAI (ChatGPT)
- Google Generative AI
- Ollama (local)
- Any HA-compatible conversation agent

If AI fails, the game uses built-in fallback puzzles.

---

## Troubleshooting

### Integration Not Found
- Restart Home Assistant after installing via HACS
- Check that `custom_components/puzzle_game` folder exists

### Puzzles Not Generating
- Verify your conversation agent is working (test in Developer Tools > Services)
- Check Home Assistant logs for errors
- Fallback puzzles will be used if AI fails

### Panel Not Showing in Sidebar
- Restart Home Assistant after adding the integration
- Check Home Assistant logs for errors

### Voice Commands Not Working
- Verify the blueprint automation is enabled
- Ensure View Assist is properly configured

---

## Manual Installation (Without HACS)

1. Copy `custom_components/puzzle_game` to your `config/custom_components/` folder
2. Restart Home Assistant
3. Add integration via Settings > Devices & Services
4. Import the blueprint

---

## Credits

- **[View Assist](https://dinki.github.io/View-Assist/)** by **[dinki](https://github.com/dinki)**
- **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** by **[msp1974](https://github.com/msp1974)**
- **Home Assistant Community**
- Icon: [Twemoji](https://github.com/twitter/twemoji) by Twitter (CC BY 4.0)

## License

MIT License - See LICENSE file for details
