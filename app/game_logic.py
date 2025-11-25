"""
Core game logic and state management
"""
import uuid
import random
from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Game, Puzzle
import config


class GameManager:
    """Manages game state and logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _ordinal(self, n):
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    def _word_description(self, word):
        """Generate description of word length (e.g., '2 words, 10 letters' or 'Word has 5 letters')"""
        words = word.split()
        word_count = len(words)
        letter_count = sum(len(w) for w in words)

        if word_count > 1:
            return f"{word_count} words, {letter_count} letters"
        else:
            return f"Word has {letter_count} letters"

    async def create_game(self, puzzle_id: int, user_id: Optional[str] = None) -> Game:
        """Create a new game session"""
        game = Game(
            id=str(uuid.uuid4()),
            puzzle_id=puzzle_id,
            user_id=user_id,
            phase=1,
            current_word_index=0,
            score=0,
            reveals=0,
            solved_words=[],
            skipped_words=[],
            revealed_letters={}
        )
        self.db.add(game)
        await self.db.commit()
        await self.db.refresh(game)
        return game

    async def get_game(self, game_id: str) -> Optional[Game]:
        """Get game by ID"""
        result = await self.db.execute(
            select(Game).where(Game.id == game_id)
        )
        return result.scalar_one_or_none()

    async def get_puzzle(self, puzzle_id: int) -> Optional[Puzzle]:
        """Get puzzle by ID"""
        result = await self.db.execute(
            select(Puzzle).where(Puzzle.id == puzzle_id)
        )
        return result.scalar_one_or_none()

    def get_current_word_blanks(self, game: Game, puzzle: Puzzle) -> str:
        """Get word blanks with revealed letters"""
        if game.phase == 2:
            # Phase 2: Final answer
            word = puzzle.theme
            revealed = game.revealed_letters.get("final", [])

            # Also include the hint position
            hint_position = game.revealed_letters.get("phase2_hint_position")
            if hint_position is not None:
                revealed = list(revealed) + [hint_position]
        else:
            # Phase 1: Current clue word
            word = puzzle.words[game.current_word_index]
            revealed = game.revealed_letters.get(str(game.current_word_index), [])

        # Build blanks with revealed letters - handle multi-word answers
        result = []
        for i, char in enumerate(word):
            if char == ' ':
                # Add clear word boundary - don't add to blanks, add directly to result
                if result:  # Remove trailing space from previous word
                    result.pop()
                result.append('   ')  # Three spaces for word gap
            elif i in revealed:
                result.append(char)
                result.append(' ')
            else:
                result.append("_")
                result.append(' ')

        # Remove trailing space
        if result and result[-1] == ' ':
            result.pop()

        return ''.join(result)

    def check_answer(self, game: Game, puzzle: Puzzle, answer: str) -> Tuple[bool, str]:
        """
        Check if answer is correct

        Returns:
            (is_correct, correct_answer)
        """
        # Normalize answer: uppercase, strip, and remove spaces for comparison
        answer = answer.upper().strip()
        answer_normalized = answer.replace(' ', '')

        if game.phase == 1:
            # Phase 1: Check current clue word
            correct_answer = puzzle.words[game.current_word_index]
            correct_normalized = correct_answer.replace(' ', '')
            return (answer_normalized == correct_normalized, correct_answer)
        else:
            # Phase 2: Check theme
            correct_answer = puzzle.theme
            correct_normalized = correct_answer.replace(' ', '')
            return (answer_normalized == correct_normalized, correct_answer)

    async def submit_answer(self, game: Game, puzzle: Puzzle, answer: str) -> Dict:
        """
        Process answer submission

        Returns dict with:
            - correct: bool
            - score_change: int
            - message: str (TTS-friendly)
            - phase_changed: bool
            - game_completed: bool
        """
        is_correct, correct_answer = self.check_answer(game, puzzle, answer)

        if not is_correct:
            # Wrong answer
            if game.phase == 1:
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
                from datetime import datetime
                game.is_active = False
                game.gave_up = False
                game.completed_at = datetime.utcnow()

                await self.db.commit()

                return {
                    "correct": False,
                    "message": f"Wrong! The answer was {correct_answer}. Final score: {game.score} out of {config.MAX_SCORE}. Better luck next time!",
                    "score_change": 0,
                    "phase_changed": False,
                    "game_completed": True
                }

        # Correct answer!
        if game.phase == 1:
            # Phase 1: Correct clue word
            game.score += config.POINTS_PER_WORD
            game.reveals += 1
            game.solved_words.append(game.current_word_index)

            # Remove from skipped_words if it was previously skipped
            if game.current_word_index in game.skipped_words:
                game.skipped_words.remove(game.current_word_index)
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(game, "skipped_words")

            # Mark JSON field as modified so SQLAlchemy saves it
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(game, "solved_words")

            # Check if all 5 words are solved
            if len(game.solved_words) >= 5:
                game.phase = 2
                game.current_word_index = 0

                solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]
                solved_words_str = ", ".join(solved_words_list)

                # Count words and letters in theme
                theme_words = puzzle.theme.split()
                word_count = len(theme_words)
                letter_count = sum(len(word) for word in theme_words)

                # Get a random position and letter for the theme (excluding spaces)
                # Store this in revealed_letters so it stays consistent
                import random
                theme_letters = [(i, c) for i, c in enumerate(puzzle.theme) if c != ' ']

                if theme_letters:
                    hint_index, revealed_letter = random.choice(theme_letters)
                    # Store the hint position in revealed_letters
                    game.revealed_letters = {"phase2_hint_position": hint_index}
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(game, "revealed_letters")
                    # Calculate letter position (excluding spaces)
                    position = len([c for c in puzzle.theme[:hint_index] if c != ' ']) + 1
                    hint_message = f"The {self._ordinal(position)} letter is {revealed_letter}."
                else:
                    game.revealed_letters = {}
                    hint_message = ""

                await self.db.commit()

                return {
                    "correct": True,
                    "message": f"Correct, {correct_answer}! You finished all 5 words. "
                               f"Now here's the real challenge. These five words are your clues: {solved_words_str}. "
                               f"The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters. "
                               f"{hint_message}",
                    "score_change": config.POINTS_PER_WORD,
                    "phase_changed": True,
                    "game_completed": False
                }
            else:
                # More words to solve - find next word
                # Priority: next unsolved word that's NOT skipped, then first skipped word

                # First, try to find next unsolved word that hasn't been skipped
                start_index = game.current_word_index
                next_index = (start_index + 1) % 5
                found_next = False

                # Look for next unsolved word that's NOT skipped
                for _ in range(5):
                    if (next_index not in game.solved_words and
                        next_index not in game.skipped_words):
                        game.current_word_index = next_index
                        found_next = True
                        break
                    next_index = (next_index + 1) % 5

                # If no unskipped unsolved word found, go to first skipped word
                if not found_next and game.skipped_words:
                    game.current_word_index = game.skipped_words[0]

                next_clue = puzzle.clues[game.current_word_index]
                next_word_desc = self._word_description(puzzle.words[game.current_word_index])

                # Ensure clue ends with proper punctuation
                if not next_clue.endswith(('.', '!', '?')):
                    next_clue = f"{next_clue}."

                await self.db.commit()

                return {
                    "correct": True,
                    "message": f"Correct, {correct_answer}! Score: {game.score}. "
                               f"Next clue: {next_clue} {next_word_desc}.",
                    "score_change": config.POINTS_PER_WORD,
                    "phase_changed": False,
                    "game_completed": False
                }

        else:
            # Phase 2: Correct final answer!
            from datetime import datetime
            game.score += config.FINAL_ANSWER_BONUS
            game.is_active = False
            game.completed_at = datetime.utcnow()

            await self.db.commit()

            perfect = game.score == config.MAX_SCORE
            message = f"Correct, {correct_answer}! Final score: {game.score} out of {config.MAX_SCORE}."
            if perfect:
                message += " Perfect game!"
            message += " You've completed today's puzzle! Say 'play bonus game' to play another round."

            return {
                "correct": True,
                "message": message,
                "score_change": config.FINAL_ANSWER_BONUS,
                "phase_changed": False,
                "game_completed": True
            }

    async def reveal_letter(self, game: Game, puzzle: Puzzle) -> Dict:
        """
        Reveal a random letter

        Returns dict with message and success status
        """
        if game.reveals <= 0:
            return {
                "success": False,
                "message": "No reveals left. Earn more by solving words correctly."
            }

        # Get current word
        if game.phase == 1:
            word = puzzle.words[game.current_word_index]
            key = str(game.current_word_index)
        else:
            word = puzzle.theme
            key = "final"

            # Phase 2 (final word): Only allow ONE manual reveal
            # Check if a manual reveal has already been used
            final_revealed = game.revealed_letters.get("final", [])
            if final_revealed:
                return {
                    "success": False,
                    "message": "No reveals allowed on the final word."
                }

        # Get already revealed positions
        revealed = list(game.revealed_letters.get(key, []))

        # For Phase 2, also exclude the hint position from being revealed again
        if game.phase == 2:
            hint_position = game.revealed_letters.get("phase2_hint_position")
            if hint_position is not None and hint_position not in revealed:
                revealed.append(hint_position)

        # Find unrevealed positions (excluding spaces)
        unrevealed = [i for i in range(len(word)) if i not in revealed and word[i] != ' ']

        if not unrevealed:
            return {
                "success": False,
                "message": "All letters already revealed."
            }

        # Reveal random letter
        pos = random.choice(unrevealed)

        # Update the revealed list for this key
        final_revealed = list(game.revealed_letters.get(key, []))
        final_revealed.append(pos)
        game.revealed_letters[key] = final_revealed
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(game, "revealed_letters")
        game.reveals -= 1

        await self.db.commit()

        blanks = self.get_current_word_blanks(game, puzzle)

        return {
            "success": True,
            "message": f"Here's a letter: {blanks}. {game.reveals} reveals left."
        }

    async def skip_word(self, game: Game, puzzle: Puzzle) -> Dict:
        """Skip current word (Phase 1 only)"""
        if game.phase != 1:
            return {
                "success": False,
                "message": "Can't skip during final answer phase."
            }

        # Add current word to skipped list if not already there
        if game.current_word_index not in game.skipped_words:
            game.skipped_words.append(game.current_word_index)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(game, "skipped_words")

        # Find next word to move to
        # Priority: next unsolved word that's NOT skipped, or if none, first skipped word

        # First, try to find next unsolved word that hasn't been skipped
        start_index = game.current_word_index
        next_index = (start_index + 1) % 5
        found_next = False

        # Look for next unsolved word that's NOT skipped
        for _ in range(5):
            if (next_index not in game.solved_words and
                next_index not in game.skipped_words and
                next_index != game.current_word_index):
                game.current_word_index = next_index
                found_next = True
                break
            next_index = (next_index + 1) % 5

        # If we didn't find an unskipped unsolved word, go to first skipped word
        if not found_next and game.skipped_words:
            # Go to the first skipped word
            game.current_word_index = game.skipped_words[0]

        next_clue = puzzle.clues[game.current_word_index]
        next_word_desc = self._word_description(puzzle.words[game.current_word_index])

        # Ensure clue ends with proper punctuation
        if not next_clue.endswith(('.', '!', '?')):
            next_clue = f"{next_clue}."

        await self.db.commit()

        return {
            "success": True,
            "message": f"Skipped. Next clue: {next_clue} {next_word_desc}.",
            "phase_changed": False
        }

    async def give_up(self, game: Game, puzzle: Puzzle) -> Dict:
        """End game and reveal all answers"""
        from datetime import datetime
        game.is_active = False
        game.gave_up = True
        game.completed_at = datetime.utcnow()

        await self.db.commit()

        # Show all answers
        all_words = ", ".join(puzzle.words)
        message = f"Game over. The words were: {all_words}. The theme was: {puzzle.theme}. Final score: {game.score}."

        return {
            "success": True,
            "message": message,
            "all_words": puzzle.words,
            "theme": puzzle.theme
        }
