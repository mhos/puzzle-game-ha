"""
Database models for Puzzle Game
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Puzzle(Base):
    """A generated puzzle with theme and words"""
    __tablename__ = "puzzles"

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(100), nullable=False)  # Final answer (e.g., "CAROUSEL")
    words = Column(JSON, nullable=False)  # List of 5 clue words
    clues = Column(JSON, nullable=False)  # List of 5 clues
    created_at = Column(DateTime, default=datetime.utcnow)
    is_daily = Column(Boolean, default=False)
    daily_date = Column(String(10), nullable=True, unique=True)  # YYYY-MM-DD format


class Game(Base):
    """A game session"""
    __tablename__ = "games"

    id = Column(String(50), primary_key=True, index=True)  # UUID
    puzzle_id = Column(Integer, nullable=False)
    user_id = Column(String(100), nullable=True)  # Optional user tracking

    # Game state
    phase = Column(Integer, default=1)  # 1 or 2
    current_word_index = Column(Integer, default=0)  # 0-4
    score = Column(Integer, default=0)
    reveals = Column(Integer, default=0)

    # Track progress
    solved_words = Column(JSON, default=list)  # List of solved word indices
    skipped_words = Column(JSON, default=list)  # List of skipped word indices
    revealed_letters = Column(JSON, default=dict)  # {word_index: [positions]}

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    gave_up = Column(Boolean, default=False)
    last_message = Column(Text, nullable=True)  # Last feedback message


class GameStats(Base):
    """User statistics (optional)"""
    __tablename__ = "game_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, unique=True)

    total_games = Column(Integer, default=0)
    games_completed = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    perfect_games = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
