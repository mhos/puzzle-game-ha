"""
Ollama client for puzzle generation
"""
import httpx
import json
import re
from typing import Dict, List
import config


class OllamaClient:
    def __init__(self):
        self.url = config.OLLAMA_URL
        self.model = config.OLLAMA_MODEL

    async def generate_puzzle(self) -> Dict[str, any]:
        """
        Generate a complete puzzle: theme + 5 words + 5 clues
        Difficulty varies by day of week:
        - Thursday: Movie theme
        - Sunday: Hardest (10/10)
        - Other days: Random difficulty 1-9

        Returns:
            {
                "theme": "CAROUSEL",
                "words": ["HORSES", "POLES", "ROTATE", "MUSIC", "CARNIVAL"],
                "clues": ["Animals you ride at a fair", ...]
            }
        """
        from datetime import datetime

        # Get current day of week (0=Monday, 6=Sunday)
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
            import random
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

        prompt = f"""You are a creative puzzle generator. Generate a unique and interesting word puzzle.

{theme_instruction}

BE CREATIVE! Think of ANY interesting theme - objects, places, activities, concepts, pop culture, history, science, etc.

Create a puzzle with these components:

1. A THEME (final answer): Choose any interesting noun or concept (4-15 letters, uppercase)
   - Can be single word: LIGHTHOUSE, TREEHOUSE, DETECTIVE, MICROSCOPE, SKATEBOARD
   - Can be two words: FERRIS WHEEL, FIRE STATION, COMIC BOOK, SOLAR SYSTEM, CORAL REEF
   - Be creative and diverse! Don't repeat common themes
   - Think about interesting objects, places, activities, animals, phenomena, etc.

2. FIVE CLUE WORDS (4-10 letters each, uppercase) that ALL strongly relate to your chosen theme
   - Must be clearly connected to the theme
   - For lower difficulty: Use more obvious words related to the theme
   - For higher difficulty: Use less obvious but still related words
   - Not synonyms of the theme
   - Each word should help players guess the theme

3. FIVE DESCRIPTIVE CLUES for each word (one sentence each)
   - Must DESCRIBE the word without revealing it directly
   - No letters, rhymes, or phonetic hints
   - Keep clues concise (under 15 words)
   - For lower difficulty: Make clues more direct and descriptive
   - For higher difficulty: Make clues require more thinking

Format your response EXACTLY like this:
THEME: SUBMARINE
WORD1: OCEAN | Large body of salt water
WORD2: PERISCOPE | Viewing device for looking above water
WORD3: TORPEDO | Underwater explosive weapon
WORD4: CAPTAIN | Person who commands the vessel
WORD5: DEPTH | How far below the surface

Now generate a completely unique and creative puzzle with a theme you've never used before:"""

        # Adjust temperature based on difficulty
        # Lower difficulty = lower temperature (more predictable/common themes)
        # Higher difficulty = higher temperature (more creative/unusual themes)
        temperature = 0.7 + (difficulty * 0.05)  # Range: 0.75 (easy) to 1.2 (hard)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "top_k": 50,
                            "top_p": 0.95,
                            "num_predict": 500
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                text = result.get("response", "")

                # Parse the response
                return self._parse_puzzle_response(text)

        except Exception as e:
            print(f"Error generating puzzle: {e}")
            # Return a fallback puzzle
            return self._get_fallback_puzzle()

    def _parse_puzzle_response(self, text: str) -> Dict[str, any]:
        """Parse LLM response into structured puzzle data"""
        try:
            lines = text.strip().split("\n")
            theme = None
            words = []
            clues = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("THEME:"):
                    theme = line.split(":", 1)[1].strip().upper()
                elif line.startswith("WORD"):
                    # Format: WORD1: HORSES | Animals you ride at a fair
                    parts = line.split(":", 1)[1].strip()
                    if "|" in parts:
                        word, clue = parts.split("|", 1)
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
                raise ValueError(f"Incomplete puzzle: theme={theme}, words={len(words)}, clues={len(clues)}")

        except Exception as e:
            print(f"Error parsing puzzle: {e}")
            return self._get_fallback_puzzle()

    def _get_fallback_puzzle(self) -> Dict[str, any]:
        """Return a hardcoded puzzle if generation fails"""
        import random

        puzzles = [
            {
                "theme": "BASEBALL",
                "words": ["PITCHER", "STRIKE", "DIAMOND", "GLOVE", "HOMERUN"],
                "clues": [
                    "Player who throws the ball to start play",
                    "When the batter misses or doesn't swing",
                    "Shape of the playing field",
                    "Leather hand protection for catching",
                    "Hitting the ball over the fence"
                ]
            },
            {
                "theme": "PIZZA",
                "words": ["CHEESE", "TOMATO", "SLICE", "CRUST", "OVEN"],
                "clues": [
                    "Dairy product that melts on top",
                    "Red fruit used for sauce",
                    "Triangular piece you eat",
                    "Baked dough on the bottom",
                    "Hot appliance for baking"
                ]
            },
            {
                "theme": "VOLCANO",
                "words": ["LAVA", "ERUPTION", "MOUNTAIN", "MAGMA", "ASH"],
                "clues": [
                    "Molten rock flowing down the sides",
                    "Explosive event from the crater",
                    "Large natural elevation of earth",
                    "Hot liquid rock underground",
                    "Fine powder particles in the air"
                ]
            },
            {
                "theme": "MOVIES",
                "words": ["SCREEN", "POPCORN", "ACTOR", "THEATER", "DIRECTOR"],
                "clues": [
                    "Large white surface for projection",
                    "Popular buttery snack",
                    "Person who plays a character",
                    "Building where films are shown",
                    "Person who leads the film production"
                ]
            },
            {
                "theme": "ELEPHANT",
                "words": ["TRUNK", "IVORY", "AFRICA", "GRAY", "MAMMAL"],
                "clues": [
                    "Long flexible nose appendage",
                    "White material from tusks",
                    "Continent where they live wild",
                    "Their typical skin color",
                    "Class of warm-blooded animals"
                ]
            },
            {
                "theme": "GUITAR",
                "words": ["STRINGS", "CHORDS", "ROCK", "ACOUSTIC", "FRET"],
                "clues": [
                    "Six thin wires you pluck",
                    "Multiple notes played together",
                    "Genre of loud music",
                    "Type without electrical amplification",
                    "Metal bars along the neck"
                ]
            },
            {
                "theme": "DOCTOR",
                "words": ["HOSPITAL", "PATIENT", "MEDICINE", "SURGERY", "NURSE"],
                "clues": [
                    "Medical facility for treatment",
                    "Person receiving medical care",
                    "Drugs prescribed for illness",
                    "Operation to fix internal problems",
                    "Healthcare worker assisting physicians"
                ]
            },
            {
                "theme": "AIRPLANE",
                "words": ["PILOT", "WINGS", "TAKEOFF", "FLIGHT", "LUGGAGE"],
                "clues": [
                    "Person who flies the aircraft",
                    "Large appendages for lift",
                    "Leaving the ground to fly",
                    "Journey through the air",
                    "Bags and suitcases you bring"
                ]
            }
        ]

        return random.choice(puzzles)


# Singleton instance
ollama_client = OllamaClient()
