import json
import winsound
import os
from utils.constants import SAVE_FILE
from game.sprites import sprite_manager

def save_sprite_mappings():
    """Save sprite mappings to a separate configuration file"""
    try:
        sprite_config = {
            "characters": sprite_manager.sprite_mappings['characters'],
            "terrain": sprite_manager.sprite_mappings['terrain'],
            "items": sprite_manager.sprite_mappings['items']
        }
        
        with open("sprite_config.json", "w") as f:
            json.dump(sprite_config, f, indent=2)  # Added indent for readability
        return True
    except Exception as e:
        print(f"Error saving sprite mappings: {e}")
        return False

def load_sprite_mappings():
    """Load sprite mappings from the configuration file"""
    try:
        if not os.path.exists("sprite_config.json"):
            return False
            
        with open("sprite_config.json", "r") as f:
            sprite_config = json.load(f)
            
        sprite_manager.sprite_mappings.update(sprite_config)
        return True
    except Exception as e:
        print(f"Error loading sprite mappings: {e}")
        return False

def play_sound(frequency, duration=200):
    """Helper function to play sound with error handling"""
    try:
        winsound.Beep(frequency, duration)
    except Exception as e:
        print(f"Sound effect failed: {e}")

def save_game(player, world):
    """Save the game state to a file"""
    try:
        save_data = {
            "player": {
                "name": player.name,
                "health": player.health,
                "max_health": player.max_health,
                "attack": player.attack,
                "level": player.level,
                "exp": player.exp,
                "kills": player.kills,
                "inventory": player.inventory.to_dict(),
                "equipment": {slot: item.to_dict() if item else None 
                            for slot, item in player.equipment.items()}
            },
            "world": {
                "player_x": world.player_x,
                "player_y": world.player_y
            }
        }
        
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def load_game():
    """Load the game state from a file"""
    try:
        if not os.path.exists("savegame.json"):
            return None
            
        with open("savegame.json", "r") as f:
            save_data = json.load(f)
        return save_data
    except Exception as e:
        print(f"Error loading game: {e}")
        return None 