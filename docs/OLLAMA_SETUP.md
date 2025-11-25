# Ollama Setup Guide

Ollama is **required** for this game to generate puzzles. This guide helps you install and configure it.

## What is Ollama?

Ollama is a tool that lets you run large language models (LLMs) locally on your computer. This game uses it to generate creative word puzzles with themes and clues.

## Installation

### Option 1: Native Installation (Recommended)

Visit https://ollama.ai/ and download the installer for your platform:

- **Linux**: `curl https://ollama.ai/install.sh | sh`
- **macOS**: Download the .dmg installer
- **Windows**: Download the .exe installer

### Option 2: Docker

```bash
docker run -d -p 11434:11434 --name ollama ollama/ollama
```

For GPU support (NVIDIA):
```bash
docker run -d --gpus all -p 11434:11434 --name ollama ollama/ollama
```

## Pull the Required Model

This game requires the `llama3.2:3b` model (approximately 2GB download):

```bash
ollama pull llama3.2:3b
```

**Why this model?**
- Small enough to run on most hardware (3 billion parameters)
- Fast generation times
- Good at creative tasks like puzzle generation
- Works well on CPU (GPU optional)

## Verify Installation

Check that Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

You should see output like:
```json
{
  "models": [
    {
      "name": "llama3.2:3b",
      ...
    }
  ]
}
```

## Configuration for Puzzle Game

### Same Machine as Game Server

If Ollama runs on the same machine as the puzzle game, the default config works:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### Different Machine

If Ollama runs on a different machine (e.g., a GPU server):

1. Make sure Ollama is accessible on your network
2. Update `.env`:
```env
OLLAMA_URL=http://192.168.1.100:11434  # Your Ollama server IP
OLLAMA_MODEL=llama3.2:3b
```

3. If using Docker for Ollama, bind to all interfaces:
```bash
docker run -d -p 0.0.0.0:11434:11434 --name ollama ollama/ollama
```

## Testing Puzzle Generation

Once Ollama is running, test puzzle generation manually:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Generate a word puzzle with a theme and 5 related words",
  "stream": false
}'
```

You should get a response with generated text.

## System Requirements

### Minimum (CPU only)
- 8GB RAM
- 4 CPU cores
- 5GB disk space (for model)

### Recommended
- 16GB RAM
- 8 CPU cores or GPU
- 10GB disk space

### GPU Acceleration (Optional)

Ollama can use GPU for faster generation:

- **NVIDIA GPU**: Automatically detected (requires CUDA)
- **Apple Silicon (M1/M2/M3)**: Automatically uses Metal
- **AMD GPU**: Linux only (requires ROCm)

## Troubleshooting

### Ollama won't start

Check if port 11434 is already in use:
```bash
lsof -i :11434  # Linux/macOS
netstat -ano | findstr :11434  # Windows
```

### Model download fails

- Check internet connection
- Ensure you have enough disk space (5GB+)
- Try pulling again: `ollama pull llama3.2:3b`

### Game can't connect to Ollama

1. Verify Ollama is running: `curl http://localhost:11434/api/tags`
2. Check the `OLLAMA_URL` in your `.env` file
3. If using Docker, ensure network connectivity between containers
4. Check firewall rules if Ollama is on a different machine

### Slow puzzle generation

- First puzzle generation is always slower (model loading)
- CPU-only systems: 10-30 seconds is normal
- With GPU: 2-5 seconds is typical
- Consider using a GPU if available for better performance

## Using Different Models

While `llama3.2:3b` is recommended, you can try other models:

```bash
# Smaller (faster, less creative)
ollama pull llama3.2:1b

# Larger (slower, more creative)
ollama pull llama3.2:7b
```

Update `.env`:
```env
OLLAMA_MODEL=llama3.2:1b  # or whatever model you prefer
```

**Note:** Larger models require more RAM and are slower but may generate better puzzles.

## Security Considerations

- Ollama runs locally, no data is sent to external servers
- The puzzle game only sends puzzle generation prompts to Ollama
- No user data or voice commands are sent to Ollama
- All AI processing happens on your local network

## Updating Ollama

```bash
# Update Ollama itself (varies by platform)
# Linux
curl https://ollama.ai/install.sh | sh

# Update models
ollama pull llama3.2:3b
```

## Alternative: Cloud Ollama

You can run Ollama on a cloud server and point the game to it, but local installation is recommended for privacy and performance.

## Getting Help

- Ollama Documentation: https://github.com/ollama/ollama
- Ollama Discord: https://discord.gg/ollama
- This project's Issues: https://github.com/mhos/puzzle-game-ha/issues
