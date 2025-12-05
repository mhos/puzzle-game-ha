"""Core game logic and state management for Puzzle Game."""
from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Any

from .const import POINTS_PER_WORD, FINAL_ANSWER_BONUS, MAX_SCORE
from .storage import PuzzleGameStorage

_LOGGER = logging.getLogger(__name__)


class GameManager:
    """Manages game state and logic."""

    def __init__(self, storage: PuzzleGameStorage) -> None:
        """Initialize game manager."""
        self.storage = storage

    @staticmethod
    def _ordinal(n: int) -> str:
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)."""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    @staticmethod
    def _word_description(word: str) -> str:
        """Generate description of word length."""
        words = word.split()
        word_count = len(words)
        letter_count = sum(len(w) for w in words)

        if word_count > 1:
            return f"{word_count} words, {letter_count} letters"
        else:
            return f"Word has {letter_count} letters"

    def get_current_word_blanks(self, game: dict) -> str:
        """Get word blanks with revealed letters."""
        puzzle = game.get("puzzle", {})

        if game["phase"] == 2:
            # Phase 2: Final answer
            word = puzzle.get("theme", "")
            revealed = game.get("revealed_letters", {}).get("final", [])

            # Also include the hint position
            hint_position = game.get("revealed_letters", {}).get("phase2_hint_position")
            if hint_position is not None:
                revealed = list(revealed) + [hint_position]
        else:
            # Phase 1: Current clue word
            words = puzzle.get("words", [])
            if game["current_word_index"] < len(words):
                word = words[game["current_word_index"]]
            else:
                word = ""
            revealed = game.get("revealed_letters", {}).get(
                str(game["current_word_index"]), []
            )

        # Build blanks with revealed letters
        result = []
        for i, char in enumerate(word):
            if char == ' ':
                if result:
                    result.pop()
                result.append('   ')
            elif i in revealed:
                result.append(char)
                result.append(' ')
            else:
                result.append("_")
                result.append(' ')

        if result and result[-1] == ' ':
            result.pop()

        return ''.join(result)

    def check_answer(self, game: dict, answer: str) -> tuple[bool, str]:
        """Check if answer is correct.

        Returns:
            (is_correct, correct_answer)
        """
        puzzle = game.get("puzzle", {})
        answer = answer.upper().strip()
        answer_normalized = answer.replace(' ', '')

        if game["phase"] == 1:
            words = puzzle.get("words", [])
            if game["current_word_index"] < len(words):
                correct_answer = words[game["current_word_index"]]
            else:
                correct_answer = ""
            correct_normalized = correct_answer.replace(' ', '')
            return (answer_normalized == correct_normalized, correct_answer)
        else:
            correct_answer = puzzle.get("theme", "")
            correct_normalized = correct_answer.replace(' ', '')
            return (answer_normalized == correct_normalized, correct_answer)

    async def submit_answer(self, game: dict, answer: str) -> dict:
        """Process answer submission.

        Returns dict with:
            - correct: bool
            - score_change: int
            - message: str (TTS-friendly)
            - phase_changed: bool
            - game_completed: bool
        """
        puzzle = game.get("puzzle", {})
        is_correct, correct_answer = self.check_answer(game, answer)

        if not is_correct:
            if game["phase"] == 1:
                word_desc = self._word_description(correct_answer)
                return {
                    "correct": False,
                    "message": f"Wrong, try again. {word_desc}.",
                    "score_change": 0,
                    "phase_changed": False,
                    "game_completed": False
                }
            else:
                # Phase 2: Wrong final answer = game over
                game["is_active"] = False
                game["gave_up"] = False
                game["completed_at"] = datetime.utcnow().isoformat()

                await self.storage.update_game(game["id"], {
                    "is_active": False,
                    "gave_up": False,
                    "completed_at": game["completed_at"]
                })

                return {
                    "correct": False,
                    "message": f"Wrong! The answer was {correct_answer}. Final score: {game['score']} out of {MAX_SCORE}. Better luck next time!",
                    "score_change": 0,
                    "phase_changed": False,
                    "game_completed": True
                }

        # Correct answer!
        if game["phase"] == 1:
            game["score"] += POINTS_PER_WORD
            game["reveals"] += 1
            game["solved_words"].append(game["current_word_index"])

            if game["current_word_index"] in game.get("skipped_words", []):
                game["skipped_words"].remove(game["current_word_index"])

            # Check if all 5 words are solved
            if len(game["solved_words"]) >= 5:
                game["phase"] = 2
                game["current_word_index"] = 0

                words = puzzle.get("words", [])
                solved_words_list = [words[i] for i in sorted(game["solved_words"]) if i < len(words)]
                solved_words_str = ", ".join(solved_words_list)

                theme = puzzle.get("theme", "")
                theme_words = theme.split()
                word_count = len(theme_words)
                letter_count = sum(len(word) for word in theme_words)

                # Generate hint for phase 2
                theme_letters = [(i, c) for i, c in enumerate(theme) if c != ' ']
                if theme_letters:
                    hint_index, revealed_letter = random.choice(theme_letters)
                    game["revealed_letters"] = {"phase2_hint_position": hint_index}
                    position = len([c for c in theme[:hint_index] if c != ' ']) + 1
                    hint_message = f"The {self._ordinal(position)} letter is {revealed_letter}."
                else:
                    game["revealed_letters"] = {}
                    hint_message = ""

                await self.storage.update_game(game["id"], {
                    "phase": 2,
                    "current_word_index": 0,
                    "score": game["score"],
                    "reveals": game["reveals"],
                    "solved_words": game["solved_words"],
                    "skipped_words": game.get("skipped_words", []),
                    "revealed_letters": game["revealed_letters"]
                })

                return {
                    "correct": True,
                    "message": f"Correct, {correct_answer}! You finished all 5 words. "
                               f"Now here's the real challenge. These five words are your clues: {solved_words_str}. "
                               f"The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters. "
                               f"{hint_message}",
                    "score_change": POINTS_PER_WORD,
                    "phase_changed": True,
                    "game_completed": False
                }
            else:
                # More words to solve - find next word
                start_index = game["current_word_index"]
                next_index = (start_index + 1) % 5
                found_next = False

                for _ in range(5):
                    if (next_index not in game["solved_words"] and
                        next_index not in game.get("skipped_words", [])):
                        game["current_word_index"] = next_index
                        found_next = True
                        break
                    next_index = (next_index + 1) % 5

                if not found_next and game.get("skipped_words"):
                    game["current_word_index"] = game["skipped_words"][0]

                clues = puzzle.get("clues", [])
                words = puzzle.get("words", [])
                if game["current_word_index"] < len(clues):
                    next_clue = clues[game["current_word_index"]]
                    next_word_desc = self._word_description(words[game["current_word_index"]])
                else:
                    next_clue = "Next clue"
                    next_word_desc = ""

                if not next_clue.endswith(('.', '!', '?')):
                    next_clue = f"{next_clue}."

                await self.storage.update_game(game["id"], {
                    "current_word_index": game["current_word_index"],
                    "score": game["score"],
                    "reveals": game["reveals"],
                    "solved_words": game["solved_words"],
                    "skipped_words": game.get("skipped_words", [])
                })

                return {
                    "correct": True,
                    "message": f"Correct, {correct_answer}! Score: {game['score']}. "
                               f"Next clue: {next_clue} {next_word_desc}.",
                    "score_change": POINTS_PER_WORD,
                    "phase_changed": False,
                    "game_completed": False
                }
        else:
            # Phase 2: Correct final answer!
            game["score"] += FINAL_ANSWER_BONUS
            game["is_active"] = False
            game["completed_at"] = datetime.utcnow().isoformat()

            await self.storage.update_game(game["id"], {
                "score": game["score"],
                "is_active": False,
                "completed_at": game["completed_at"]
            })

            perfect = game["score"] == MAX_SCORE
            message = f"Correct, {correct_answer}! Final score: {game['score']} out of {MAX_SCORE}."
            if perfect:
                message += " Perfect game!"
            message += " You've completed the puzzle! Say 'play bonus game' to play another round."

            return {
                "correct": True,
                "message": message,
                "score_change": FINAL_ANSWER_BONUS,
                "phase_changed": False,
                "game_completed": True
            }

    async def reveal_letter(self, game: dict) -> dict:
        """Reveal a random letter."""
        puzzle = game.get("puzzle", {})

        if game["reveals"] <= 0:
            return {
                "success": False,
                "message": "No reveals left. Earn more by solving words correctly."
            }

        if game["phase"] == 1:
            words = puzzle.get("words", [])
            if game["current_word_index"] < len(words):
                word = words[game["current_word_index"]]
            else:
                word = ""
            key = str(game["current_word_index"])
        else:
            word = puzzle.get("theme", "")
            key = "final"

            # Phase 2: Only allow ONE manual reveal
            final_revealed = game.get("revealed_letters", {}).get("final", [])
            if final_revealed:
                return {
                    "success": False,
                    "message": "No reveals allowed on the final word."
                }

        revealed = list(game.get("revealed_letters", {}).get(key, []))

        # For Phase 2, exclude hint position
        if game["phase"] == 2:
            hint_position = game.get("revealed_letters", {}).get("phase2_hint_position")
            if hint_position is not None and hint_position not in revealed:
                revealed.append(hint_position)

        unrevealed = [i for i in range(len(word)) if i not in revealed and word[i] != ' ']

        if not unrevealed:
            return {
                "success": False,
                "message": "All letters already revealed."
            }

        pos = random.choice(unrevealed)

        if "revealed_letters" not in game:
            game["revealed_letters"] = {}

        final_revealed = list(game.get("revealed_letters", {}).get(key, []))
        final_revealed.append(pos)
        game["revealed_letters"][key] = final_revealed
        game["reveals"] -= 1

        await self.storage.update_game(game["id"], {
            "revealed_letters": game["revealed_letters"],
            "reveals": game["reveals"]
        })

        blanks = self.get_current_word_blanks(game)

        return {
            "success": True,
            "message": f"Here's a letter: {blanks}. {game['reveals']} reveals left."
        }

    async def skip_word(self, game: dict) -> dict:
        """Skip current word (Phase 1 only)."""
        puzzle = game.get("puzzle", {})

        if game["phase"] != 1:
            return {
                "success": False,
                "message": "Can't skip during final answer phase."
            }

        if "skipped_words" not in game:
            game["skipped_words"] = []

        if game["current_word_index"] not in game["skipped_words"]:
            game["skipped_words"].append(game["current_word_index"])

        # Find next word - first try unskipped words, then cycle through skipped
        start_index = game["current_word_index"]
        next_index = (start_index + 1) % 5
        found_next = False

        # First pass: look for words that haven't been skipped or solved
        for _ in range(5):
            if (next_index not in game["solved_words"] and
                next_index not in game["skipped_words"]):
                game["current_word_index"] = next_index
                found_next = True
                break
            next_index = (next_index + 1) % 5

        # Second pass: if all remaining words are skipped, cycle through them
        if not found_next and game["skipped_words"]:
            # Find the next skipped word after current position
            current_pos = game["skipped_words"].index(start_index) if start_index in game["skipped_words"] else -1
            next_pos = (current_pos + 1) % len(game["skipped_words"])
            game["current_word_index"] = game["skipped_words"][next_pos]

        clues = puzzle.get("clues", [])
        words = puzzle.get("words", [])
        if game["current_word_index"] < len(clues):
            next_clue = clues[game["current_word_index"]]
            next_word_desc = self._word_description(words[game["current_word_index"]])
        else:
            next_clue = "Next clue"
            next_word_desc = ""

        if not next_clue.endswith(('.', '!', '?')):
            next_clue = f"{next_clue}."

        await self.storage.update_game(game["id"], {
            "current_word_index": game["current_word_index"],
            "skipped_words": game["skipped_words"]
        })

        return {
            "success": True,
            "message": f"Skipped. Next clue: {next_clue} {next_word_desc}.",
            "phase_changed": False
        }

    async def give_up(self, game: dict) -> dict:
        """End game and reveal all answers."""
        puzzle = game.get("puzzle", {})

        game["is_active"] = False
        game["gave_up"] = True
        game["completed_at"] = datetime.utcnow().isoformat()

        await self.storage.update_game(game["id"], {
            "is_active": False,
            "gave_up": True,
            "completed_at": game["completed_at"]
        })

        words = puzzle.get("words", [])
        theme = puzzle.get("theme", "")
        all_words = ", ".join(words)
        message = f"Game over. The words were: {all_words}. The theme was: {theme}. Final score: {game['score']}."

        return {
            "success": True,
            "message": message,
            "all_words": words,
            "theme": theme
        }

    def get_current_clue(self, game: dict) -> str:
        """Get the current clue text for TTS."""
        puzzle = game.get("puzzle", {})
        clues = puzzle.get("clues", [])
        words = puzzle.get("words", [])
        theme = puzzle.get("theme", "")

        if game["phase"] == 1:
            if game["current_word_index"] < len(clues):
                clue = clues[game["current_word_index"]]
                word_desc = self._word_description(words[game["current_word_index"]])
                if not clue.endswith(('.', '!', '?')):
                    clue = f"{clue}."
                return f"{clue} {word_desc}."
            return "No clue available"
        else:
            # Phase 2 - show solved words as reminder
            solved_words_list = [words[i] for i in sorted(game["solved_words"]) if i < len(words)]
            solved_words_str = ", ".join(solved_words_list) if solved_words_list else "none"

            theme_words = theme.split()
            word_count = len(theme_words)
            letter_count = sum(len(word) for word in theme_words)

            hint_position = game.get("revealed_letters", {}).get("phase2_hint_position")
            if hint_position is not None and hint_position < len(theme):
                revealed_letter = theme[hint_position]
                position = len([c for c in theme[:hint_position] if c != ' ']) + 1
                return (f"Your clues are: {solved_words_str}. The theme has {word_count} "
                        f"word{'s' if word_count != 1 else ''} and {letter_count} letters. "
                        f"The {self._ordinal(position)} letter is {revealed_letter}.")
            else:
                return (f"Your clues are: {solved_words_str}. The theme has {word_count} "
                        f"word{'s' if word_count != 1 else ''} and {letter_count} letters.")

    def get_game_state_dict(self, game: dict) -> dict:
        """Convert game to state dictionary for sensor."""
        puzzle = game.get("puzzle", {})
        words = puzzle.get("words", [])
        theme = puzzle.get("theme", "")

        solved_words_list = [words[i] for i in sorted(game.get("solved_words", [])) if i < len(words)]

        return {
            "game_id": game.get("id", ""),
            "phase": game.get("phase", 1),
            "word_number": game.get("current_word_index", 0) + 1 if game.get("phase") == 1 else 6,
            "score": game.get("score", 0),
            "reveals": game.get("reveals", 0),
            "blanks": self.get_current_word_blanks(game),
            "clue": self.get_current_clue(game),
            "solved_words": solved_words_list,
            "solved_word_indices": list(game.get("solved_words", [])),
            "is_active": game.get("is_active", False),
            "last_message": game.get("last_message"),
            "theme_revealed": theme if not game.get("is_active") else None,
        }
