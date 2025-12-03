"""AI client for puzzle generation using Home Assistant conversation agent."""
from __future__ import annotations

import logging
import random
import re
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.conversation import async_converse

from .const import FALLBACK_PUZZLES

_LOGGER = logging.getLogger(__name__)


def get_puzzle_prompt() -> tuple[str, int]:
    """Generate the puzzle prompt based on day of week.

    Returns:
        Tuple of (prompt string, difficulty level)
    """
    day_of_week = datetime.now().weekday()

    # Thursday = 3, Sunday = 6
    if day_of_week == 3:  # Thursday - Movie theme
        theme_instruction = """THURSDAY SPECIAL - MOVIE THEME:
Your theme MUST be a famous movie, film franchise, or movie-related concept.
Examples: STAR WARS, JAWS, TITANIC, MARVEL, PIXAR, HOLLYWOOD, CINEMA, etc.
Difficulty: Medium (5/10) - Make it recognizable but not too obvious."""
        difficulty = 5
    elif day_of_week == 6:  # Sunday - Hardest
        theme_instruction = """SUNDAY CHALLENGE - HARDEST PUZZLE:
Choose an obscure or complex theme. Make it challenging!
Difficulty: 10/10 - Use uncommon themes and tricky clues."""
        difficulty = 10
    else:  # Other days - Random difficulty
        difficulty = random.randint(1, 9)
        if difficulty <= 3:
            theme_instruction = f"""EASY PUZZLE (Difficulty {difficulty}/10):
Choose a common, everyday theme that most people would know.
Use simple, straightforward clues."""
        elif difficulty <= 6:
            theme_instruction = f"""MEDIUM PUZZLE (Difficulty {difficulty}/10):
Choose a moderately familiar theme.
Make clues clear but not too obvious."""
        else:
            theme_instruction = f"""HARD PUZZLE (Difficulty {difficulty}/10):
Choose a less common but still recognizable theme.
Make clues more challenging and require some thought."""

    prompt = f"""You are a creative puzzle generator. Generate a unique word puzzle.

{theme_instruction}

Create a puzzle with these components:

1. A THEME (final answer): Choose any interesting noun or concept (4-15 letters, uppercase)
   - Can be single word: LIGHTHOUSE, TREEHOUSE, DETECTIVE, MICROSCOPE
   - Can be two words: FERRIS WHEEL, FIRE STATION, COMIC BOOK
   - Be creative and diverse!

2. FIVE CLUE WORDS (4-10 letters each, uppercase) that ALL strongly relate to your theme
   - Must be clearly connected to the theme
   - Not synonyms of the theme
   - Each word should help players guess the theme

3. FIVE DESCRIPTIVE CLUES for each word (one sentence each)
   - Must DESCRIBE the word without revealing it directly
   - No letters, rhymes, or phonetic hints
   - Keep clues concise (under 15 words)

Format your response EXACTLY like this:
THEME: SUBMARINE
WORD1: OCEAN | Large body of salt water
WORD2: PERISCOPE | Viewing device for looking above water
WORD3: TORPEDO | Underwater explosive weapon
WORD4: CAPTAIN | Person who commands the vessel
WORD5: DEPTH | How far below the surface

Generate a creative puzzle now:"""

    return prompt, difficulty


def parse_puzzle_response(text: str) -> dict | None:
    """Parse LLM response into structured puzzle data.

    Args:
        text: Raw text response from the AI

    Returns:
        Puzzle dict with theme, words, clues or None if parsing failed
    """
    try:
        lines = text.strip().split("\n")
        theme = None
        words = []
        clues = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.upper().startswith("THEME:"):
                theme = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("WORD"):
                # Format: WORD1: HORSES | Animals you ride at a fair
                parts = line.split(":", 1)
                if len(parts) > 1:
                    word_clue = parts[1].strip()
                    if "|" in word_clue:
                        word, clue = word_clue.split("|", 1)
                        words.append(word.strip().upper())
                        clues.append(clue.strip())

        # Validate we got everything
        if theme and len(words) == 5 and len(clues) == 5:
            return {
                "theme": theme,
                "words": words,
                "clues": clues
            }
        else:
            _LOGGER.warning(
                "Incomplete puzzle: theme=%s, words=%d, clues=%d",
                theme, len(words), len(clues)
            )
            return None

    except Exception as e:
        _LOGGER.error("Error parsing puzzle response: %s", e)
        return None


def get_fallback_puzzle() -> dict:
    """Return a random fallback puzzle."""
    return random.choice(FALLBACK_PUZZLES).copy()


async def generate_puzzle(
    hass: HomeAssistant,
    conversation_agent: str | None = None
) -> dict:
    """Generate a puzzle using Home Assistant's conversation agent.

    Args:
        hass: Home Assistant instance
        conversation_agent: Optional specific agent to use

    Returns:
        Puzzle dict with theme, words, clues
    """
    prompt, difficulty = get_puzzle_prompt()

    try:
        # Use HA's conversation service
        result = await async_converse(
            hass=hass,
            text=prompt,
            conversation_id=None,
            context=None,
            language=None,
            agent_id=conversation_agent,
        )

        if result and result.response:
            # Get the response text
            response_text = result.response.speech.get("plain", {}).get("speech", "")

            if response_text:
                puzzle = parse_puzzle_response(response_text)
                if puzzle:
                    _LOGGER.info("Successfully generated puzzle with theme: %s", puzzle["theme"])
                    return puzzle

        _LOGGER.warning("AI response did not contain valid puzzle, using fallback")

    except Exception as e:
        _LOGGER.error("Error generating puzzle via conversation agent: %s", e)

    # Return fallback puzzle
    return get_fallback_puzzle()
