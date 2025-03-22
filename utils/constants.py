import pygame
import random

# Constants for the game window
CELL_SIZE = 60
GRID_SIZE = 10
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
WINDOW_TITLE = "Simple RPG"
SAVE_FILE = "player_save.json"  # File to store save data

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
DARK_GREEN = (0, 100, 0)  # Darker green for terrain
HEALTH_GREEN = (0, 200, 0)  # Brighter green for health bars
GOLD_COLOR = (255, 215, 0)  # Color for gold items

# Font settings
FONT_SIZE = 24
FONT = None  # Will be initialized in World class

# Item rarities and their colors
RARITY_COLORS = {
    "common": WHITE,
    "uncommon": (0, 255, 0),  # Green
    "rare": (0, 128, 255),    # Blue
    "epic": (128, 0, 255),    # Purple
    "legendary": (255, 128, 0) # Orange
}

# Terrain types
TERRAIN_GRASS = 0
TERRAIN_FOREST = 1
TERRAIN_MOUNTAIN = 2
TERRAIN_WATER = 3

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_COMBAT = "combat"
STATE_INVENTORY = "inventory"
STATE_SAVE = "save"
STATE_LOAD = "load"
STATE_QUIT = "quit"

# Sound effects
SOUND_BUTTON_CLICK = "assets/sounds/pour_glass_water.wav"
SOUND_LEVEL_UP = "assets/sounds/pour_glass_water.wav"
SOUND_ITEM_PICKUP = "assets/sounds/pour_glass_water.wav"
SOUND_COMBAT_START = "assets/sounds/CivilWarDrummer.wav"
SOUND_COMBAT_END = "assets/sounds/pour_glass_water.wav"
SOUND_ATTACK = "assets/sounds/Swords_Collide.wav"
SOUND_HIT = "assets/sounds/Swords_Collide.wav"
SOUND_MISS = "assets/sounds/pour_glass_water.wav"
SOUND_DEATH = "assets/sounds/NeckBreaking.wav"
SOUND_VICTORY = "assets/sounds/pour_glass_water.wav"
SOUND_SPELL_CAST = "assets/sounds/pour_glass_water.wav"
SOUND_SPELL_HIT = "assets/sounds/Swords_Collide.wav"
SOUND_HEAL = "assets/sounds/pour_glass_water.wav"

# Spell types
SPELL_TYPE_DAMAGE = "damage"
SPELL_TYPE_HEAL = "heal"
SPELL_TYPE_BUFF = "buff"

# Spell elements
SPELL_ELEMENT_FIRE = "fire"
SPELL_ELEMENT_ICE = "ice"
SPELL_ELEMENT_LIGHTNING = "lightning"
SPELL_ELEMENT_HOLY = "holy"
SPELL_ELEMENT_WIND = "wind"

# Loot tables for different enemy types
LOOT_TABLES = {
    "Goblin": [
        (0.8, {"type": "gold", "min": 1, "max": 10}),
        (0.3, {"type": "resource", "name": "Goblin Ear", "value": 5}),
        (0.1, {"type": "weapon", "name": "Rusty Dagger", "attack": 2})
    ],
    "Orc": [
        (0.9, {"type": "gold", "min": 5, "max": 20}),
        (0.4, {"type": "resource", "name": "Orc Tooth", "value": 10}),
        (0.2, {"type": "weapon", "name": "Orc Axe", "attack": 4})
    ],
    "Troll": [
        (1.0, {"type": "gold", "min": 10, "max": 30}),
        (0.5, {"type": "resource", "name": "Troll Hide", "value": 20}),
        (0.3, {"type": "armor", "name": "Troll Leather", "defense": 3})
    ],
    "Dragon": [
        (1.0, {"type": "gold", "min": 50, "max": 100}),
        (0.7, {"type": "resource", "name": "Dragon Scale", "value": 50}),
        (0.4, {"type": "weapon", "name": "Dragon Fang", "attack": 8}),
        (0.4, {"type": "armor", "name": "Dragon Scale Mail", "defense": 6})
    ]
}

MAX_CONSOLE_MESSAGES = 100  # Maximum number of messages to store in console history 