# Blueprint-Ready Version

This is an experimental version of the puzzle game following recommendations from dinki (View Assist creator) for easier distribution via blueprints.

## Key Differences from Original

### Original Version (`puzzle_game.yaml.example`)
- 12 separate automations
- Each voice command is its own automation
- User says wake word before every command
- Traditional approach, works great but harder to distribute

### Blueprint Version (`puzzle_game_blueprint.yaml`)
- **1 main automation** with consolidated triggers
- **1 script** for active game loop
- **2 state automations** for dashboard management
- Uses `assist_satellite.ask_question` for continuous conversation
- **NO wake word spam** - continuous back-and-forth during gameplay

## How It Works

### Continuous Conversation Flow

**User says:** "Start puzzle game"

**System:** Starts game, shows dashboard, announces first clue

**Then enters a loop where the system asks:** "What would you like to do?"

**User can respond** (NO wake word needed):
- "dog" or "the answer is dog" → Submits answer
- "reveal" → Reveals a letter
- "skip" → Skips current word
- "repeat" → Repeats the clue
- "pause" → Exits the loop, saves game state
- "give up" → Ends the game (asks for confirmation)

**After each action**, the system responds and asks again, maintaining the conversation flow.

### Pause & Resume

Users can say "pause" to exit the active session. The game state is preserved.

Later, they can say "continue puzzle game" to resume where they left off and re-enter the conversation loop.

## File Structure

```yaml
# Input Helpers
- puzzle_game_id (tracks current game)
- puzzle_last_satellite (tracks device)
- puzzle_game_session_active (tracks if in active loop)
- puzzle_game_give_up_pending (confirmation state)
- timer for 10-minute timeout

# REST Commands (same as original)
- All 7 API calls to backend

# REST Sensors (same as original)
- Latest game sensor
- Game state sensor

# Script
- puzzle_game_active_session
  └─ Main game loop using ask_question
     └─ Handles all in-game commands
        └─ Loops until pause/give up/game ends

# Automations
1. puzzle_game_controller (main)
   - Trigger: start/bonus/continue
   - Calls the script to begin loop

2. puzzle_game_hide_dashboard
   - Hides dashboard 60s after game ends

3. puzzle_game_reset_timeout
   - Resets 10-minute timer on interaction
```

## Advantages for Distribution

### For Blueprints
1. **Single automation** is easier to convert to blueprint
2. **Fewer entities** for users to manage (3 automations vs 12)
3. **Cleaner UI** - less clutter in HA automations list

### For Users
1. **Better UX** - No wake word spam during gameplay
2. **Natural conversation flow** - More like talking to a person
3. **Pause/resume** - Still supports the "come back later" feature
4. **Easier troubleshooting** - One place to debug vs many

## Next Steps

### To Convert to Blueprint:
1. Add `blueprint` section with inputs:
   ```yaml
   blueprint:
     name: Puzzle Game for View Assist
     description: Voice-controlled word puzzle game
     input:
       api_host:
         name: API Server Host
         description: IP address of your puzzle game server
         default: "192.168.1.100"
       api_port:
         name: API Server Port
         default: 5000
   ```

2. Replace `YOUR_API_HOST:5000` with:
   ```yaml
   http://{{ api_host }}:{{ api_port }}
   ```

3. Add more customization inputs:
   - Game timeout duration
   - Enable/disable buzzer sound
   - Custom messages

### To Test:
1. Disable the original `puzzle_game.yaml.example` package
2. Enable this `puzzle_game_blueprint.yaml` package
3. Replace `YOUR_API_HOST:5000` with your server
4. Restart Home Assistant
5. Say "start puzzle game" and test the conversation flow

## Limitations

### Database Persistence
The current version still relies on the Python backend's SQLite database for:
- Game state persistence
- Score tracking
- Puzzle history
- Resume functionality

This is fine for single-installation use, but for pure HA-only distribution, you might need to:
- Store game state in HA input helpers
- Use HA database for persistence
- Or accept that users need the backend API running

### ask_question Behavior
- The assist popup/bar appears during `ask_question` prompts
- This is a View Assist UI behavior
- Could potentially be customized via View Assist settings

## Credits

Special thanks to **[dinki](https://github.com/dinki)** (View Assist creator) for the architecture recommendations and examples from the number guessing game.

## Feedback

This is experimental! Please test and provide feedback:
- Does the conversation flow feel natural?
- Is pause/resume working as expected?
- Any issues with ask_question behavior?
- Would you prefer this approach vs the original?
