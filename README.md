# Voice-Activated Puzzle Game for Home Assistant

A voice-controlled word puzzle game that integrates with Home Assistant, [View Assist](https://dinki.github.io/View-Assist/) by [dinki](https://github.com/dinki), and the [View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App) by [msp1974](https://github.com/msp1974). Solve themed word puzzles completely hands-free!

> **⚠️ CRITICAL REQUIREMENTS:**
>
> This game requires BOTH of the following to be installed and working BEFORE you can play:
> 1. **[View Assist](https://dinki.github.io/View-Assist/)** - Home Assistant integration
> 2. **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** - Application running on your display device
>
> You MUST have both installed and configured. This will NOT work with standard Home Assistant Assist alone.

## Features

- 🎮 **Daily Puzzles**: Fresh AI-generated puzzle every day
- 🎁 **Unlimited Bonus Rounds**: Play as many bonus games as you want
- 🗣️ **Voice Control**: Completely hands-free gameplay via Home Assistant voice assistants
- 📺 **Visual Dashboard**: Real-time display powered by [View Assist](https://dinki.github.io/View-Assist/)
- 💾 **Persistent State**: Resume games anytime within 24 hours
- 🎯 **Smart Gameplay**: Skip words, reveal letters, and track your score
- 🔊 **Audio Feedback**: Wrong answer buzzer and TTS announcements

## How It Works

Each puzzle consists of 5 themed words plus a final "connection" answer:
1. Solve 5 word clues (10 points each)
2. Earn letter reveals for correct answers
3. Use reveals to get hints when stuck (costs points!)
4. Skip difficult words and return to them later
5. Guess the theme that connects all 5 words (20 point bonus)

## Architecture

- **Backend**: Python FastAPI server with SQLAlchemy ORM
- **AI**: Ollama (llama3.2:3b) generates puzzles with themes and clues
- **Database**: SQLite for game state persistence
- **Frontend**: Real-time HTML dashboard
- **Integration**: Home Assistant conversation platform + View Assist

## Requirements

### Critical Requirements - MUST BE INSTALLED FIRST

Before installing this game, you **MUST** have both of these installed and working:

1. **[View Assist](https://dinki.github.io/View-Assist/)** - Home Assistant integration by [dinki](https://github.com/dinki)
2. **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** - Device application by [msp1974](https://github.com/msp1974)

**These are NOT optional. You need BOTH working together.**

### Hardware

- **Home Assistant server** (any platform)
- **Display device running View Assist Companion App** - Supports:
  - Android tablets
  - Android phones
  - Other devices compatible with View Assist Companion App
- **Server to run the FastAPI backend** (can be same as HA server, Raspberry Pi, Docker host, etc.)

### Software
- **Home Assistant 2024.x or newer**
- **[View Assist](https://dinki.github.io/View-Assist/)** - REQUIRED
- **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** - REQUIRED
- **Python 3.11+** (if running without Docker)
- **Docker & Docker Compose** (recommended deployment method)
- **Ollama** with llama3.2:3b model - **You must install and run this yourself!**

### What is View Assist?

View Assist is a two-part system that works together to create a smart voice-controlled display:

1. **[View Assist](https://dinki.github.io/View-Assist/)** by [dinki](https://github.com/dinki) - The Home Assistant integration that provides the backend services and functionality
2. **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** by [msp1974](https://github.com/msp1974) - The application that runs on your display device (Android tablets/phones)

**BOTH components are required and work together to provide:**
- Visual dashboards displayed on your device's screen
- Custom voice commands and automations
- Wake word detection and voice control
- Broadcasting messages across multiple devices
- Integration with Home Assistant dashboards

**This game requires BOTH components to:**
- Display the interactive game dashboard on your device
- Trigger game-specific voice commands
- Show real-time game state, clues, and scores

**YOU MUST INSTALL AND CONFIGURE BOTH BEFORE USING THIS GAME:**
1. **First:** Install View Assist integration in Home Assistant - [dinki.github.io/View-Assist](https://dinki.github.io/View-Assist/)
2. **Second:** Install the Companion App on your Android device - [github.com/msp1974/ViewAssist_Companion_App](https://github.com/msp1974/ViewAssist_Companion_App)
3. **Then:** Follow the setup guides to connect them together

## Quick Start

### 1. Install Ollama (Required First!)

Before installing this game, you **must** have Ollama running somewhere accessible to the game server.

**Quick Install:**
- Visit https://ollama.ai/ and follow installation instructions for your platform
- Or use their Docker image: `docker run -d -p 11434:11434 ollama/ollama`

**Pull the required model:**
```bash
ollama pull llama3.2:3b
```

**Verify it's working:**
```bash
curl http://localhost:11434/api/tags
```

You should see `llama3.2:3b` in the list of models.

📖 **Need help with Ollama?** See the detailed [Ollama Setup Guide](docs/OLLAMA_SETUP.md)

### 2. Clone the Repository

```bash
git clone https://github.com/mhos/puzzle-game-ha.git
cd puzzle-game-ha
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your Ollama URL
# Example: OLLAMA_URL=http://192.168.1.100:11434
```

**Important:** If Ollama is running on a different machine, update `OLLAMA_URL` in `.env` to point to it.

### 4. Deploy with Docker Compose

```bash
docker-compose up -d
```

This will start the Puzzle Game API server on port 5000.

### 5. Configure Home Assistant

#### Add Package Support (if not already enabled)

Edit your `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

#### Install the Puzzle Game Package

```bash
# Copy the example package file
cp homeassistant/packages/puzzle_game.yaml.example /config/packages/puzzle_game.yaml

# Edit the file and replace YOUR_API_HOST with your server's IP/hostname
# Example: Change http://YOUR_API_HOST:5000 to http://192.168.1.100:5000
```

#### Restart Home Assistant

Check Configuration → Server Controls → Restart

### 6. Test the Game

Say to your View Assist device:
- "Start puzzle game"
- "The answer is [word]"
- "Reveal a letter"
- "Skip word"
- "Play bonus game"

## Voice Commands

| Command | Action |
|---------|--------|
| "Start puzzle game" | Start or resume daily puzzle |
| "Play bonus game" | Start or resume bonus round |
| "The answer is [word]" | Submit an answer |
| "Is it [word]" | Alternative answer format |
| "Reveal a letter" | Use a reveal to get a hint |
| "Skip word" | Skip current word |
| "Repeat the clue" | Hear the clue again |
| "Give up" | End the game (asks for confirmation) |

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

The package file (`puzzle_game.yaml`) requires one configuration change:
- Replace `YOUR_API_HOST:5000` with your server's IP address and port

Example: `http://192.168.1.100:5000`

## Manual Installation (Without Docker)

### 1. Install and Setup Ollama (Required!)

Follow instructions at [ollama.ai](https://ollama.ai/) to install Ollama for your platform.

Pull the required model:
```bash
ollama pull llama3.2:3b
```

Make sure Ollama is running (default port 11434).

### 2. Install Python Dependencies

```bash
cd app
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if your Ollama is not on localhost:11434
```

### 4. Start the Server

```bash
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

### 5. Follow Home Assistant setup from step 5 in Quick Start above

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
│       └── wrong.mp3        # Wrong answer sound
├── homeassistant/
│   └── packages/
│       └── puzzle_game.yaml.example  # HA configuration
├── docker-compose.yml       # Docker orchestration
├── .env.example            # Environment variables template
└── README.md               # This file
```

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

### Ollama issues
- See the [Ollama Setup Guide](docs/OLLAMA_SETUP.md) for detailed troubleshooting
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check that llama3.2:3b model is installed: `ollama list`

### Game doesn't start
- Verify the API server is accessible from Home Assistant
- Check that OLLAMA_URL in .env points to your Ollama instance
- Check Home Assistant logs for errors

### Dashboard doesn't appear
- Ensure View Assist integration is configured
- Verify the API host URL in puzzle_game.yaml is correct
- Check that port 5000 is accessible from your View Assist device

### Wrong answer buzzer doesn't play
- Verify wrong.mp3 exists in app/static/
- Check media_player entity ID matches your View Assist device

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

Built for the Home Assistant community with love ❤️
