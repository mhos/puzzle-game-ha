# Home Assistant Setup Guide

This guide walks you through configuring Home Assistant to work with the Puzzle Game.

## Prerequisites

**YOU MUST HAVE THESE INSTALLED AND WORKING BEFORE PROCEEDING:**

1. **Home Assistant 2024.x or newer**
2. **[View Assist](https://dinki.github.io/View-Assist/) integration** - REQUIRED, created by [dinki](https://github.com/dinki)
3. **[View Assist Companion App](https://github.com/msp1974/ViewAssist_Companion_App)** - REQUIRED, created by [msp1974](https://github.com/msp1974), running on your display device
4. **Puzzle Game API server** running and accessible from your Home Assistant instance

**BOTH View Assist components (the HA integration AND the device app) MUST be installed, configured, and working together.**

### Why BOTH View Assist Components are Required

View Assist is a two-part system:
- **View Assist integration** - Runs in Home Assistant, provides the services and backend
- **View Assist Companion App** - Runs on your Android device, provides the display and interface

**This game absolutely requires BOTH components because:**

- Uses the `view_assist.set_state` and `view_assist.navigate` services (from the HA integration)
- Uses the `view_assist_entity()` function to identify your display device
- Requires the Companion App running on your device to show the dashboard
- Leverages View Assist's conversation platform for game-specific voice commands
- Displays real-time visual feedback on your voice assistant's screen

Standard Home Assistant Assist (without View Assist) does NOT have these capabilities.

**If you haven't installed View Assist yet, STOP HERE and install both components first:**
1. **First:** Install View Assist integration in Home Assistant - [dinki.github.io/View-Assist](https://dinki.github.io/View-Assist/)
2. **Second:** Install the Companion App on your Android device - [github.com/msp1974/ViewAssist_Companion_App](https://github.com/msp1974/ViewAssist_Companion_App)
3. **Third:** Configure them to work together following the View Assist setup guides
4. **Finally:** Return here once View Assist is working

## Step 1: Enable Packages

If you haven't already enabled the packages feature, edit your `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

## Step 2: Create Packages Directory

```bash
mkdir -p /config/packages
```

## Step 3: Install Puzzle Game Package

1. Copy the example configuration:
```bash
cp puzzle_game.yaml.example /config/packages/puzzle_game.yaml
```

2. Edit `/config/packages/puzzle_game.yaml` and replace all instances of `YOUR_API_HOST:5000` with your server's IP address and port.

For example, if your API server is at `192.168.1.100`:
```yaml
url: "http://192.168.1.100:5000/api/game/start"
```

You'll need to update this in several places:
- All `rest_command` URLs
- Both `rest` sensor resources
- View Assist dashboard URLs in automations

### Quick Replace Command

You can use this command to do a find-replace:

```bash
sed -i 's/YOUR_API_HOST:5000/192.168.1.100:5000/g' /config/packages/puzzle_game.yaml
```

Just replace `192.168.1.100:5000` with your actual server address.

## Step 4: Check Configuration

Before restarting, check your configuration:
1. Go to **Developer Tools** → **YAML**
2. Click **Check Configuration**
3. Fix any errors that appear

## Step 5: Restart Home Assistant

Go to **Settings** → **System** → **Restart**

## Step 6: Verify Setup

After restart, you should see these new entities:

### Input Text
- `input_text.puzzle_game_id`
- `input_text.puzzle_current_message`
- `input_text.puzzle_last_satellite`

### Input Boolean
- `input_boolean.puzzle_game_give_up_pending`

### Timer
- `timer.puzzle_game_timeout`

### Sensors
- `sensor.puzzle_latest_game`
- `sensor.puzzle_game_state`

### Automations
- Puzzle Game - Start New Game
- Puzzle Game - Submit Answer
- Puzzle Game - Reveal Letter
- Puzzle Game - Skip Word
- Puzzle Game - Repeat Clue
- Puzzle Game - Give Up (and confirmation automations)
- Puzzle Game - Start Bonus Game
- Several View Assist integration automations

## Step 7: Test the Game

1. Go to your View Assist device
2. Say: "Start puzzle game"
3. The dashboard should appear and you should hear the first clue

## Troubleshooting

### "Entity not available" errors

Check that the API server is running and accessible:
```bash
curl http://YOUR_API_HOST:5000/
```

Should return: `{"status":"ok","service":"Puzzle Game API"}`

### Dashboard doesn't appear

1. Verify View Assist integration is working (try other View Assist commands)
2. Check that the dashboard URL is correct in automations
3. Verify the game actually started by checking `sensor.puzzle_latest_game`

### Automations don't trigger

1. Check that conversation triggers are enabled for your View Assist device
2. Test with the simple test automation in the package
3. Check Home Assistant logs for errors

### REST sensors showing errors

Check Home Assistant logs for the specific error. Common issues:
- API server not accessible
- Wrong URL in configuration
- Firewall blocking access

## Customization

### Changing Voice Commands

Edit the `command` lists in the automation triggers. For example, to add "begin puzzle":

```yaml
trigger:
  - platform: conversation
    command:
      - "start puzzle game"
      - "[start] [a] [new] puzzle [game]"
      - "begin puzzle"  # Add your custom command
```

### Adjusting Timeouts

The game has a 10-minute inactivity timeout. To change it, edit:

```yaml
timer:
  puzzle_game_timeout:
    duration: "00:10:00"  # Change to desired duration
```

And update the timer start actions in automations.

### Changing Dashboard Display Time

After completing a game, the dashboard stays visible for 60 seconds. To change:

Find the "Hide Dashboard" automation and edit the delay:

```yaml
- delay:
    seconds: 60  # Change this value
```

## Uninstalling

To remove the puzzle game:

1. Delete the package file:
```bash
rm /config/packages/puzzle_game.yaml
```

2. Restart Home Assistant

3. Optionally, clean up any remaining entities from the UI:
   - Go to Settings → Devices & Services → Entities
   - Search for "puzzle"
   - Delete any remaining entities

## Next Steps

- Check out the API documentation in `docs/API.md`
- See gameplay tips in the main README.md
- Join the discussion on the Home Assistant forum
