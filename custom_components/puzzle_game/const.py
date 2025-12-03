"""Constants for the Puzzle Game integration."""

DOMAIN = "puzzle_game"

# Game scoring
POINTS_PER_WORD = 10
FINAL_ANSWER_BONUS = 20
MAX_SCORE = 70  # 5 words * 10 + 20 bonus

# Storage keys
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Sensor
SENSOR_NAME = "Puzzle Game"

# Services
SERVICE_START_GAME = "start_game"
SERVICE_SUBMIT_ANSWER = "submit_answer"
SERVICE_REVEAL_LETTER = "reveal_letter"
SERVICE_SKIP_WORD = "skip_word"
SERVICE_REPEAT_CLUE = "repeat_clue"
SERVICE_GIVE_UP = "give_up"
SERVICE_SET_SESSION = "set_session"

# Attributes
ATTR_GAME_ID = "game_id"
ATTR_PHASE = "phase"
ATTR_WORD_NUMBER = "word_number"
ATTR_SCORE = "score"
ATTR_REVEALS = "reveals"
ATTR_BLANKS = "blanks"
ATTR_CLUE = "clue"
ATTR_SOLVED_WORDS = "solved_words"
ATTR_SOLVED_WORD_INDICES = "solved_word_indices"
ATTR_IS_ACTIVE = "is_active"
ATTR_LAST_MESSAGE = "last_message"
ATTR_THEME_REVEALED = "theme_revealed"
ATTR_SESSION_ACTIVE = "session_active"

# Config
CONF_CONVERSATION_AGENT = "conversation_agent"

# Default fallback puzzles (used when AI fails)
FALLBACK_PUZZLES = [
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
    },
    {
        "theme": "OCEAN",
        "words": ["WAVES", "SALT", "FISH", "CORAL", "TIDE"],
        "clues": [
            "Rolling movements of water",
            "Mineral that makes it taste different",
            "Swimming creatures with gills",
            "Colorful underwater reef builders",
            "Daily rise and fall of water level"
        ]
    },
    {
        "theme": "BIRTHDAY",
        "words": ["CAKE", "CANDLES", "GIFTS", "PARTY", "BALLOONS"],
        "clues": [
            "Sweet dessert with frosting",
            "You blow these out and make a wish",
            "Wrapped presents from friends",
            "Celebration with guests",
            "Inflated decorations that float"
        ]
    }
]
