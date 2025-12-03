# Voice-Activated Puzzle Game for Home Assistant

A voice-controlled word puzzle game that integrates with Home Assistant, [View Assist](https://dinki.github.io/View-Assist/) by [dinki](https://github.com/dinki), and the [View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App) by [msp1974](https://github.com/msp1974). Solve themed word puzzles completely hands-free!

> **CRITICAL REQUIREMENTS:**
>
> This game requires BOTH of the following to be installed and working BEFORE you can play:
> 1. **[View Assist](https://dinki.github.io/View-Assist/)** - Home Assistant integration
> 2. **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** - Application running on your display device
>
> You MUST have both installed and configured. This will NOT work with standard Home Assistant Assist alone.

## Features

- **Daily Puzzles**: Fresh AI-generated puzzle every day
- **Unlimited Bonus Rounds**: Play as many bonus games as you want
- **Voice Control**: Completely hands-free gameplay via Home Assistant voice assistants
- **Continuous Conversation**: No wake word needed during gameplay!
- **Visual Dashboard**: Real-time display powered by [View Assist](https://dinki.github.io/View-Assist/)
- **Persistent State**: Resume games anytime within 24 hours
- **Smart Gameplay**: Skip words, reveal letters, spell answers, and track your score
- **Audio Feedback**: Wrong answer buzzer, startup music, and TTS announcements

## How It Works

Each puzzle consists of 5 themed words plus a final "connection" answer:
1. Solve 5 word clues (10 points each)
2. Earn letter reveals for correct answers
3. Use reveals to get hints when stuck (costs points!)
4. Skip difficult words and return to them later
5. Guess the theme that connects all 5 words (20 point bonus)

---

## Installation

### Prerequisites

Before installing, ensure you have:

1. **[View Assist](https://dinki.github.io/View-Assist/)** installed in Home Assistant
2. **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** running on your display device
3. **[Ollama](https://ollama.ai/)** with `llama3.2:3b` model installed
4. **Home Assistant 2024.x or newer**

### Step 1: Install Ollama

```bash
# Install Ollama (visit ollama.ai for your platform)
# Then pull the required model:
ollama pull llama3.2:3b
```

### Step 2: Deploy the Game Server

```bash
git clone https://github.com/mhos/puzzle-game-ha.git
cd puzzle-game-ha
cp .env.example .env
# Edit .env and set OLLAMA_URL to your Ollama server
docker-compose up -d
```

The server will start on port 5000.

### Step 3: Install the Home Assistant Package

1. **Enable packages** in your `configuration.yaml` (if not already):
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. **Copy the package file** to your Home Assistant config:
   ```bash
   cp homeassistant/packages/puzzle_game.yaml /config/packages/
   ```

3. **Restart Home Assistant**

4. **Configure the API URL**:
   - Go to **Settings > Devices & Services > Helpers**
   - Find **"Puzzle Game API URL"**
   - Click it and set the value to your server address (e.g., `http://192.168.1.100:5000`)

### Step 4: Import the Blueprint

1. Go to **Settings > Automations & Scenes > Blueprints**
2. Click **Import Blueprint**
3. Paste this URL:
   ```
   https://github.com/mhos/puzzle-game-ha/blob/main/homeassistant/blueprints/automation/puzzle_game_controller.yaml
   ```
4. Click **Preview** then **Import**
5. Click **Create Automation** from the blueprint

That's it! The satellite device is automatically detected when you start the game.

---

## Playing the Game

### Starting a Game

Say to your View Assist device:
- **"Start puzzle game"** - Begin a new daily puzzle
- **"Play bonus game"** - Start a bonus round
- **"Continue puzzle game"** - Resume a paused game

### During Gameplay (No Wake Word Needed!)

Once the game starts, you can speak directly without saying the wake word:

| Command | Action |
|---------|--------|
| Say the word directly | Submit your answer |
| "The answer is [word]" | Alternative way to answer |
| "Spell" | Enter spelling mode (say letters one by one, then "done") |
| "Reveal" | Use a reveal to get a letter hint |
| "Skip" | Skip current word |
| "Repeat" | Hear the clue again |
| "Pause" | Pause the game (resume later with "continue puzzle game") |
| "Give up" | End the game |

### Spelling Mode

Having trouble with pronunciation? Say "spell" to enter spelling mode:
1. Say each letter one at a time: "D" ... "O" ... "G"
2. Say "done" when finished
3. The system will announce and submit your spelled word

---

## Architecture

- **Backend**: Python FastAPI server with SQLAlchemy ORM
- **AI**: Ollama (llama3.2:3b) generates puzzles with themes and clues
- **Database**: SQLite for game state persistence
- **Frontend**: Real-time HTML dashboard
- **Integration**: Home Assistant Blueprint + Package + View Assist

## Project Structure

```
puzzle-game-ha/
├── app/
│   ├── main.py              # FastAPI application
│   ├── game_logic.py        # Game state management
│   ├── models.py            # Database models
│   ├── database.py          # Database connection
│   ├── ollama_client.py     # Ollama API client
│   ├── config.py            # Configuration
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Container definition
│   └── static/
│       ├── dashboard.html   # Game dashboard
│       ├── startgame.mp3    # Startup music
│       └── wrong.mp3        # Wrong answer sound
├── homeassistant/
│   ├── packages/
│   │   └── puzzle_game.yaml           # HA package (helpers, scripts, automations)
│   └── blueprints/
│       └── automation/
│           └── puzzle_game_controller.yaml  # HA blueprint
├── docker-compose.yml       # Docker orchestration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Configuration

### Backend Configuration (.env)

```env
# Ollama API endpoint
OLLAMA_URL=http://localhost:11434

# Model to use for puzzle generation
OLLAMA_MODEL=llama3.2:3b

# Database path
DATABASE_URL=sqlite+aiosqlite:///./data/puzzle_game.db

# Server settings
HOST=0.0.0.0
PORT=5000
```

### Home Assistant Configuration

The only user configuration needed is the **Puzzle Game API URL** helper. Set this through the Home Assistant UI:
- Settings > Devices & Services > Helpers > "Puzzle Game API URL"
- Example: `http://192.168.1.100:5000`

## API Endpoints

- `GET /` - Health check
- `POST /api/game/start` - Start/resume game
- `GET /api/game/latest` - Get latest game ID
- `GET /api/game/{game_id}` - Get game state
- `POST /api/game/{game_id}/answer` - Submit answer
- `POST /api/game/{game_id}/reveal` - Reveal letter
- `POST /api/game/{game_id}/skip` - Skip word
- `POST /api/game/{game_id}/repeat` - Repeat clue
- `POST /api/game/{game_id}/giveup` - Give up

## Troubleshooting

### Ollama Issues
- See the [Ollama Setup Guide](docs/OLLAMA_SETUP.md) for detailed troubleshooting
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check that llama3.2:3b model is installed: `ollama list`

### Game Doesn't Start
- Verify the API server is accessible from Home Assistant
- Check that **Puzzle Game API URL** helper is set correctly
- Check Home Assistant logs for errors

### Dashboard Doesn't Appear
- Ensure View Assist integration is configured
- Verify the API URL helper value is correct
- Check that port 5000 is accessible from your View Assist device

### Voice Commands Not Working During Gameplay
- Make sure the blueprint automation was created after importing
- Check that `script.puzzle_game_active_session` exists (from the package)
- Verify your assist satellite supports `ask_question`

### Wrong Answer Buzzer Doesn't Play
- Verify wrong.mp3 exists in app/static/
- Check media_player entity ID matches your View Assist device

## Manual Installation (Without Docker)

```bash
cd app
pip install -r requirements.txt
cp ../.env.example ../.env
# Edit .env if your Ollama is not on localhost:11434
python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

Then follow the Home Assistant setup steps above.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - See LICENSE file for details

## Credits

This project would not be possible without:

- **[View Assist](https://dinki.github.io/View-Assist/)** by **[dinki](https://github.com/dinki)** - For creating the amazing View Assist integration that makes visual voice assistants possible
- **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** by **[msp1974](https://github.com/msp1974)** - For the Android companion app that powers the display functionality
- **[Ollama](https://ollama.ai/)** - For enabling local AI puzzle generation
- **Home Assistant Community** - For building an incredible smart home platform

Built for the Home Assistant community with love
