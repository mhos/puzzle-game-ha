"""
Puzzle Game FastAPI Server
"""
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import os

from database import get_db, init_db
from models import Puzzle, Game
from ollama_client import ollama_client
from game_logic import GameManager
import config


def ordinal(n):
    """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def word_description(word):
    """Generate description of word length (e.g., '2 words, 10 letters' or 'Word has 5 letters')"""
    words = word.split()
    word_count = len(words)
    letter_count = sum(len(w) for w in words)

    if word_count > 1:
        return f"{word_count} words, {letter_count} letters"
    else:
        return f"Word has {letter_count} letters"


app = FastAPI(title="Puzzle Game API", version="1.0.0")

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic models for requests/responses
class StartGameRequest(BaseModel):
    user_id: Optional[str] = None
    bonus: bool = False


class SubmitAnswerRequest(BaseModel):
    answer: str


class GameStateResponse(BaseModel):
    game_id: str
    phase: int
    word_number: int
    score: int
    reveals: int
    blanks: str
    clue: str
    solved_words: list
    solved_word_indices: list  # Indices of solved words (0-4)
    is_active: bool
    theme_revealed: Optional[str] = None
    last_message: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    game_state: Optional[GameStateResponse] = None


# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await init_db()
    print("Database initialized")


# Health check endpoint
@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "Puzzle Game API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Game endpoints
@app.post("/api/game/start", response_model=ActionResponse)
async def start_game(
    request: StartGameRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start or continue today's daily puzzle

    This endpoint:
    1. Checks if today's daily puzzle exists
    2. If no daily puzzle, generates one for today
    3. Checks if user has an active game for today's puzzle
    4. If completed today's puzzle, asks about bonus game
    5. Otherwise continues or starts today's puzzle
    """
    try:
        from sqlalchemy import select
        from datetime import datetime

        today = datetime.utcnow().strftime("%Y-%m-%d")

        # If bonus game requested, check for existing active bonus game first
        if request.bonus:
            # Check for any active bonus game (non-daily)
            result = await db.execute(
                select(Game)
                .join(Puzzle, Game.puzzle_id == Puzzle.id)
                .where(Puzzle.is_daily == False)
                .where(Game.is_active == True)
                .order_by(Game.started_at.desc())
            )
            existing_bonus_game = result.scalar_one_or_none()

            if existing_bonus_game:
                # Resume existing bonus game
                manager = GameManager(db)
                bonus_puzzle = await manager.get_puzzle(existing_bonus_game.puzzle_id)

                if existing_bonus_game.phase == 1:
                    current_clue = bonus_puzzle.clues[existing_bonus_game.current_word_index]
                    word_desc = word_description(bonus_puzzle.words[existing_bonus_game.current_word_index])
                    if not current_clue.endswith(('.', '!', '?')):
                        current_clue = f"{current_clue}."
                    current_clue_with_hint = f"{current_clue} {word_desc}."
                    blanks = manager.get_current_word_blanks(existing_bonus_game, bonus_puzzle)
                else:
                    # Phase 2 - build full clue with solved words
                    solved_words_list = [bonus_puzzle.words[i] for i in sorted(existing_bonus_game.solved_words)]
                    solved_words_str = ", ".join(solved_words_list) if solved_words_list else "none"
                    theme_words = bonus_puzzle.theme.split()
                    word_count = len(theme_words)
                    letter_count = sum(len(word) for word in theme_words)

                    hint_position = existing_bonus_game.revealed_letters.get("phase2_hint_position")
                    if hint_position is not None:
                        revealed_letter = bonus_puzzle.theme[hint_position]
                        position = hint_position + 1
                        blanks = manager.get_current_word_blanks(existing_bonus_game, bonus_puzzle)
                        current_clue_with_hint = f"Congratulations! You've solved: {solved_words_str}. Now for the final answer. The theme connects all five words. It has {word_count} words and {letter_count} letters. Here's a hint: letter {position} is {revealed_letter}. {blanks}."
                    else:
                        blanks = manager.get_current_word_blanks(existing_bonus_game, bonus_puzzle)
                        current_clue_with_hint = f"Congratulations! You've solved: {solved_words_str}. Now for the final answer. The theme connects all five words. It has {word_count} words and {letter_count} letters. {blanks}."

                game_state = GameStateResponse(
                    game_id=existing_bonus_game.id,
                    phase=existing_bonus_game.phase,
                    word_number=existing_bonus_game.current_word_index + 1,
                    score=existing_bonus_game.score,
                    reveals=existing_bonus_game.reveals,
                    blanks=blanks,
                    clue=current_clue_with_hint,
                    solved_words=[bonus_puzzle.words[i] for i in existing_bonus_game.solved_words],
                    solved_word_indices=existing_bonus_game.solved_words,
                    is_active=existing_bonus_game.is_active
                )

                return ActionResponse(
                    success=True,
                    message=f"Continuing your bonus game. {current_clue_with_hint}",
                    game_state=game_state
                )

            # No existing bonus game, create a new one
            puzzle_data = await ollama_client.generate_puzzle()
            bonus_puzzle = Puzzle(
                theme=puzzle_data["theme"],
                words=puzzle_data["words"],
                clues=puzzle_data["clues"],
                is_daily=False,
                daily_date=None
            )
            db.add(bonus_puzzle)
            await db.commit()
            await db.refresh(bonus_puzzle)

            # Create new bonus game
            manager = GameManager(db)
            game = await manager.create_game(bonus_puzzle.id, request.user_id)

            # Get initial state
            first_clue = bonus_puzzle.clues[0]
            first_word_desc = word_description(bonus_puzzle.words[0])
            blanks = manager.get_current_word_blanks(game, bonus_puzzle)

            game_state = GameStateResponse(
                game_id=game.id,
                phase=game.phase,
                word_number=game.current_word_index + 1,
                score=game.score,
                reveals=game.reveals,
                blanks=blanks,
                clue=first_clue,
                solved_words=[],
                solved_word_indices=[],
                is_active=game.is_active
            )

            # Ensure clue ends with proper punctuation
            if not first_clue.endswith(('.', '!', '?')):
                first_clue = f"{first_clue}."
            message = f"Bonus round! First clue: {first_clue} {first_word_desc}."

            return ActionResponse(
                success=True,
                message=message,
                game_state=game_state
            )

        # Get or create today's daily puzzle
        result = await db.execute(
            select(Puzzle)
            .where(Puzzle.is_daily == True)
            .where(Puzzle.daily_date == today)
        )
        daily_puzzle = result.scalar_one_or_none()

        if not daily_puzzle:
            # Generate today's daily puzzle
            puzzle_data = await ollama_client.generate_puzzle()
            daily_puzzle = Puzzle(
                theme=puzzle_data["theme"],
                words=puzzle_data["words"],
                clues=puzzle_data["clues"],
                is_daily=True,
                daily_date=today
            )
            db.add(daily_puzzle)
            await db.commit()
            await db.refresh(daily_puzzle)

        # Check if user has already completed today's daily puzzle
        result = await db.execute(
            select(Game)
            .join(Puzzle, Game.puzzle_id == Puzzle.id)
            .where(Puzzle.daily_date == today)
            .where(Puzzle.is_daily == True)
            .where(Game.is_active == False)
            .where(Game.completed_at.isnot(None))
        )
        completed_game = result.scalar_one_or_none()

        if completed_game:
            # User already finished today's puzzle
            return ActionResponse(
                success=False,
                message="You've already completed today's puzzle! Say 'play bonus game' if you want to play another round.",
                game_state=None
            )

        # Check for existing active game
        result = await db.execute(
            select(Game)
            .where(Game.puzzle_id == daily_puzzle.id)
            .where(Game.is_active == True)
            .order_by(Game.started_at.desc())
        )
        active_games = result.scalars().all()

        # Clean up: keep only the most recent active game for this puzzle
        if len(active_games) > 1:
            existing_game = active_games[0]
            for old_game in active_games[1:]:
                old_game.is_active = False
            await db.commit()
        elif len(active_games) == 1:
            existing_game = active_games[0]
        else:
            existing_game = None

        if existing_game:
            # Continue existing game
            manager = GameManager(db)
            puzzle = await manager.get_puzzle(existing_game.puzzle_id)

            if existing_game.phase == 1:
                current_clue = puzzle.clues[existing_game.current_word_index]
                word_desc = word_description(puzzle.words[existing_game.current_word_index])
                # Ensure clue ends with proper punctuation
                if not current_clue.endswith(('.', '!', '?')):
                    current_clue = f"{current_clue}."
                current_clue_with_hint = f"{current_clue} {word_desc}."
                blanks = manager.get_current_word_blanks(existing_game, puzzle)
            else:
                # Phase 2 - build full clue with solved words
                solved_words_list = [puzzle.words[i] for i in sorted(existing_game.solved_words)]
                solved_words_str = ", ".join(solved_words_list) if solved_words_list else "none"
                theme_words = puzzle.theme.split()
                word_count = len(theme_words)
                letter_count = sum(len(word) for word in theme_words)

                hint_position = existing_game.revealed_letters.get("phase2_hint_position")
                if hint_position is not None:
                    revealed_letter = puzzle.theme[hint_position]
                    position = hint_position + 1
                    current_clue_with_hint = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters. The {ordinal(position)} letter is {revealed_letter}."
                else:
                    current_clue_with_hint = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters."

                blanks = manager.get_current_word_blanks(existing_game, puzzle)

            solved_words_list = [puzzle.words[i] for i in sorted(existing_game.solved_words)]

            game_state = GameStateResponse(
                game_id=existing_game.id,
                phase=existing_game.phase,
                word_number=existing_game.current_word_index + 1 if existing_game.phase == 1 else 6,
                score=existing_game.score,
                reveals=existing_game.reveals,
                blanks=blanks,
                clue=current_clue_with_hint,
                solved_words=solved_words_list,
                solved_word_indices=list(existing_game.solved_words),
                is_active=existing_game.is_active
            )

            message = f"Continuing today's puzzle. {current_clue_with_hint}"

            return ActionResponse(
                success=True,
                message=message,
                game_state=game_state
            )

        # Start new game with today's daily puzzle
        manager = GameManager(db)
        game = await manager.create_game(daily_puzzle.id, request.user_id)

        # Get initial state
        first_clue = daily_puzzle.clues[0]
        first_word_desc = word_description(daily_puzzle.words[0])
        blanks = manager.get_current_word_blanks(game, daily_puzzle)

        game_state = GameStateResponse(
            game_id=game.id,
            phase=game.phase,
            word_number=game.current_word_index + 1,
            score=game.score,
            reveals=game.reveals,
            blanks=blanks,
            clue=first_clue,
            solved_words=[],
            solved_word_indices=[],
            is_active=game.is_active
        )

        # Ensure clue ends with proper punctuation
        if not first_clue.endswith(('.', '!', '?')):
            first_clue = f"{first_clue}."
        message = f"New puzzle! First clue: {first_clue} {first_word_desc}."

        return ActionResponse(
            success=True,
            message=message,
            game_state=game_state
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")


@app.get("/api/game/latest")
async def get_latest_game(db: AsyncSession = Depends(get_db)):
    """Get the most recently created active game"""
    from sqlalchemy import select

    # Get most recent ACTIVE game only (same logic as /api/game/start)
    result = await db.execute(
        select(Game)
        .where(Game.is_active == True)
        .order_by(Game.started_at.desc())
        .limit(1)
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="No active games found")

    return {"game_id": game.id}


@app.get("/api/game/{game_id}", response_model=GameStateResponse)
async def get_game_state(
    game_id: str = Path(..., description="Game ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get current game state"""
    manager = GameManager(db)
    game = await manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    puzzle = await manager.get_puzzle(game.puzzle_id)

    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    # Build current clue
    if game.phase == 1:
        if game.current_word_index < len(puzzle.clues):
            current_clue = puzzle.clues[game.current_word_index]
            word_desc = word_description(puzzle.words[game.current_word_index])
            # Ensure clue ends with proper punctuation
            if not current_clue.endswith(('.', '!', '?')):
                current_clue = f"{current_clue}."
            current_clue = f"{current_clue} {word_desc}."
        else:
            current_clue = "Moving to final answer..."
    else:
        # Phase 2 - show all solved words as reminder
        # If solved_words is empty, assume all 5 words were solved
        if not game.solved_words or len(game.solved_words) == 0:
            solved_words_list = puzzle.words[:5]
        else:
            solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]

        solved_words_str = ", ".join(solved_words_list)

        # Count words and letters in theme
        theme_words = puzzle.theme.split()
        word_count = len(theme_words)
        letter_count = sum(len(word) for word in theme_words)

        # Get the stored hint position from revealed_letters
        hint_position = game.revealed_letters.get("phase2_hint_position")

        # Fallback: if hint position not stored (old game), generate and store it now
        if hint_position is None:
            import random
            from sqlalchemy.orm.attributes import flag_modified
            theme_letters = [(i, c) for i, c in enumerate(puzzle.theme) if c != ' ']
            if theme_letters:
                hint_position, _ = random.choice(theme_letters)
                game.revealed_letters["phase2_hint_position"] = hint_position
                flag_modified(game, "revealed_letters")
                await db.commit()
                await db.refresh(game)

        if hint_position is not None:
            revealed_letter = puzzle.theme[hint_position]
            # Calculate letter position (excluding spaces)
            position = len([c for c in puzzle.theme[:hint_position] if c != ' ']) + 1
            current_clue = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters. The {ordinal(position)} letter is {revealed_letter}."
        else:
            current_clue = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters."

    # Get solved words for display
    if game.phase == 2 and (not game.solved_words or len(game.solved_words) == 0):
        solved_words_list = puzzle.words[:5]
    else:
        solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]

    blanks = manager.get_current_word_blanks(game, puzzle)

    return GameStateResponse(
        game_id=game.id,
        phase=game.phase,
        word_number=game.current_word_index + 1 if game.phase == 1 else 6,
        score=game.score,
        reveals=game.reveals,
        blanks=blanks,
        clue=current_clue,
        solved_words=solved_words_list,
        solved_word_indices=list(game.solved_words),
        is_active=game.is_active,
        theme_revealed=puzzle.theme if not game.is_active else None,
        last_message=game.last_message
    )


@app.post("/api/game/{game_id}/answer", response_model=ActionResponse)
async def submit_answer(
    game_id: str,
    request: SubmitAnswerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer"""
    manager = GameManager(db)
    game = await manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not game.is_active:
        raise HTTPException(status_code=400, detail="Game is not active")

    puzzle = await manager.get_puzzle(game.puzzle_id)

    result = await manager.submit_answer(game, puzzle, request.answer)

    # Store the feedback message
    game.last_message = result["message"]
    await db.commit()

    # Refresh game state
    await db.refresh(game)

    # Build current clue after answer
    if not game.is_active:
        # Game is complete
        current_clue = result["message"]
    elif game.phase == 1 and game.current_word_index < len(puzzle.clues):
        current_clue = puzzle.clues[game.current_word_index]
        word_desc = word_description(puzzle.words[game.current_word_index])
        # Ensure clue ends with proper punctuation
        if not current_clue.endswith(('.', '!', '?')):
            current_clue = f"{current_clue}."
        current_clue = f"{current_clue} {word_desc}."
    elif game.phase == 2:
        # Get solved words for Phase 2 clue
        if not game.solved_words or len(game.solved_words) == 0:
            solved_words_list_temp = puzzle.words[:5]
        else:
            solved_words_list_temp = [puzzle.words[i] for i in sorted(game.solved_words)]

        solved_words_str = ", ".join(solved_words_list_temp)
        theme_words = puzzle.theme.split()
        word_count = len(theme_words)
        letter_count = sum(len(word) for word in theme_words)

        hint_position = game.revealed_letters.get("phase2_hint_position")
        if hint_position is not None:
            revealed_letter = puzzle.theme[hint_position]
            position = hint_position + 1
            current_clue = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters. The {ordinal(position)} letter is {revealed_letter}."
        else:
            current_clue = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters."
    else:
        current_clue = "Game in progress"

    solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]

    # Show full theme when game is complete, otherwise show blanks
    if not game.is_active:
        blanks = puzzle.theme
    else:
        blanks = manager.get_current_word_blanks(game, puzzle)

    game_state = GameStateResponse(
        game_id=game.id,
        phase=game.phase,
        word_number=game.current_word_index + 1 if game.phase == 1 else 6,
        score=game.score,
        reveals=game.reveals,
        blanks=blanks,
        clue=current_clue,
        solved_words=solved_words_list,
        solved_word_indices=list(game.solved_words),
        is_active=game.is_active,
        theme_revealed=puzzle.theme if not game.is_active else None,
        last_message=game.last_message
    )

    return ActionResponse(
        success=result["correct"],
        message=result["message"],
        game_state=game_state
    )


@app.post("/api/game/{game_id}/reveal", response_model=ActionResponse)
async def reveal_letter(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Reveal a random letter"""
    manager = GameManager(db)
    game = await manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not game.is_active:
        raise HTTPException(status_code=400, detail="Game is not active")

    puzzle = await manager.get_puzzle(game.puzzle_id)

    result = await manager.reveal_letter(game, puzzle)

    # Store the message
    game.last_message = result["message"]
    await db.commit()
    await db.refresh(game)

    if game.phase == 1:
        current_clue = puzzle.clues[game.current_word_index]
    else:
        current_clue = "What connects all these words?"

    solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]
    blanks = manager.get_current_word_blanks(game, puzzle)

    game_state = GameStateResponse(
        game_id=game.id,
        phase=game.phase,
        word_number=game.current_word_index + 1 if game.phase == 1 else 6,
        score=game.score,
        reveals=game.reveals,
        blanks=blanks,
        clue=current_clue,
        solved_words=solved_words_list,
        solved_word_indices=list(game.solved_words),
        is_active=game.is_active,
        last_message=game.last_message
    )

    return ActionResponse(
        success=result["success"],
        message=result["message"],
        game_state=game_state
    )


@app.post("/api/game/{game_id}/skip", response_model=ActionResponse)
async def skip_word(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Skip current word (Phase 1 only)"""
    manager = GameManager(db)
    game = await manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not game.is_active:
        raise HTTPException(status_code=400, detail="Game is not active")

    puzzle = await manager.get_puzzle(game.puzzle_id)

    result = await manager.skip_word(game, puzzle)

    # Store the message
    game.last_message = result["message"]
    await db.commit()
    await db.refresh(game)

    if game.phase == 1 and game.current_word_index < len(puzzle.clues):
        current_clue = puzzle.clues[game.current_word_index]
    else:
        current_clue = "What connects all these words?"

    solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]
    blanks = manager.get_current_word_blanks(game, puzzle)

    game_state = GameStateResponse(
        game_id=game.id,
        phase=game.phase,
        word_number=game.current_word_index + 1 if game.phase == 1 else 6,
        score=game.score,
        reveals=game.reveals,
        blanks=blanks,
        clue=current_clue,
        solved_words=solved_words_list,
        solved_word_indices=list(game.solved_words),
        is_active=game.is_active,
        last_message=game.last_message
    )

    return ActionResponse(
        success=result["success"],
        message=result["message"],
        game_state=game_state
    )


@app.post("/api/game/{game_id}/giveup", response_model=ActionResponse)
async def give_up(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Give up and end game"""
    manager = GameManager(db)
    game = await manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    puzzle = await manager.get_puzzle(game.puzzle_id)

    result = await manager.give_up(game, puzzle)

    # Store the message
    game.last_message = result["message"]
    await db.commit()
    await db.refresh(game)

    game_state = GameStateResponse(
        game_id=game.id,
        phase=game.phase,
        word_number=6,
        score=game.score,
        reveals=game.reveals,
        blanks=puzzle.theme,
        clue="Game ended",
        solved_words=[puzzle.words[i] for i in sorted(game.solved_words)],
        solved_word_indices=list(game.solved_words),
        is_active=False,
        theme_revealed=puzzle.theme,
        last_message=game.last_message
    )

    return ActionResponse(
        success=True,
        message=result["message"],
        game_state=game_state
    )


@app.post("/api/game/{game_id}/repeat", response_model=ActionResponse)
async def repeat_clue(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Repeat current clue"""
    manager = GameManager(db)
    game = await manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    puzzle = await manager.get_puzzle(game.puzzle_id)

    if game.phase == 1:
        clue = puzzle.clues[game.current_word_index]
        word_desc = word_description(puzzle.words[game.current_word_index])
        # Ensure clue ends with proper punctuation
        if not clue.endswith(('.', '!', '?')):
            clue = f"{clue}."
        message = f"{clue} {word_desc}."
    else:
        # Phase 2 - repeat with full details
        if not game.solved_words or len(game.solved_words) == 0:
            solved_words_list = puzzle.words[:5]
        else:
            solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]

        solved_words_str = ", ".join(solved_words_list)

        # Count words and letters in theme
        theme_words = puzzle.theme.split()
        word_count = len(theme_words)
        letter_count = sum(len(word) for word in theme_words)

        # Get the stored hint position from revealed_letters
        hint_position = game.revealed_letters.get("phase2_hint_position")

        # Fallback: if hint position not stored (old game), generate and store it now
        if hint_position is None:
            import random
            from sqlalchemy.orm.attributes import flag_modified
            theme_letters = [(i, c) for i, c in enumerate(puzzle.theme) if c != ' ']
            if theme_letters:
                hint_position, _ = random.choice(theme_letters)
                game.revealed_letters["phase2_hint_position"] = hint_position
                flag_modified(game, "revealed_letters")
                await db.commit()
                await db.refresh(game)

        if hint_position is not None:
            revealed_letter = puzzle.theme[hint_position]
            # Calculate letter position (excluding spaces)
            position = len([c for c in puzzle.theme[:hint_position] if c != ' ']) + 1
            message = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters. The {ordinal(position)} letter is {revealed_letter}."
        else:
            message = f"Your clues are: {solved_words_str}. The theme has {word_count} word{'s' if word_count != 1 else ''} and {letter_count} letters."

    blanks = manager.get_current_word_blanks(game, puzzle)
    solved_words_list = [puzzle.words[i] for i in sorted(game.solved_words)]

    game_state = GameStateResponse(
        game_id=game.id,
        phase=game.phase,
        word_number=game.current_word_index + 1 if game.phase == 1 else 6,
        score=game.score,
        reveals=game.reveals,
        blanks=blanks,
        clue=clue if game.phase == 1 else "What connects all these words?",
        solved_words=solved_words_list,
        solved_word_indices=list(game.solved_words),
        is_active=game.is_active
    )

    return ActionResponse(
        success=True,
        message=message,
        game_state=game_state
    )


# Serve dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the game dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
