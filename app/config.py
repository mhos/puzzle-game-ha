"""
Configuration settings for Puzzle Game server
"""
import os

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://docker.bmn.lan:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/puzzle_game.db")

# Game settings
POINTS_PER_WORD = 10
FINAL_ANSWER_BONUS = 20
MAX_SCORE = 70  # 5 words * 10 + 20 bonus

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
