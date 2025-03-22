import json
import winsound
import os
from utils.constants import SAVE_FILE
from game.sprites import sprite_manager
import pygame
import wave
import struct
import math

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

def generate_tone(frequency, duration, volume=0.5, sample_rate=44100):
    """Generate a simple sine wave tone without numpy"""
    num_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        sample = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)
    
    return samples

def play_wave_sound(sound_path, duration=None):
    """Play a WAV sound file with fallback to beep"""
    try:
        # Try to play the WAV file
        if os.path.exists(sound_path):
            sound = pygame.mixer.Sound(sound_path)
            sound.play()
        else:
            # If file doesn't exist, use fallback beep
            if "attack" in sound_path.lower():
                winsound.Beep(440, 100)  # A4 note, 100ms
            elif "hit" in sound_path.lower():
                winsound.Beep(880, 100)  # A5 note, 100ms
            elif "miss" in sound_path.lower():
                winsound.Beep(220, 100)  # A3 note, 100ms
            elif "heal" in sound_path.lower():
                winsound.Beep(660, 100)  # E5 note, 100ms
            elif "combat" in sound_path.lower():
                winsound.Beep(550, 100)  # C#5 note, 100ms
            else:
                winsound.Beep(440, 100)  # Default A4 note
    except Exception as e:
        print(f"Failed to play sound file {sound_path}: {e}")
        # Fallback to beep based on sound type
        try:
            if "attack" in sound_path.lower():
                winsound.Beep(440, 100)  # A4 note, 100ms
            elif "hit" in sound_path.lower():
                winsound.Beep(880, 100)  # A5 note, 100ms
            elif "miss" in sound_path.lower():
                winsound.Beep(220, 100)  # A3 note, 100ms
            elif "heal" in sound_path.lower():
                winsound.Beep(660, 100)  # E5 note, 100ms
            elif "combat" in sound_path.lower():
                winsound.Beep(550, 100)  # C#5 note, 100ms
            else:
                winsound.Beep(440, 100)  # Default A4 note
        except Exception as e:
            print(f"Failed to play fallback sound: {e}")

def play_sound(frequency, duration=None):
    """Play a sound with the given frequency and duration"""
    try:
        if isinstance(frequency, str):
            # If frequency is a string, treat it as a sound file path
            play_wave_sound(frequency)
        else:
            # Otherwise, play a beep at the given frequency
            winsound.Beep(int(frequency), int(duration * 1000) if duration else 100)
    except Exception as e:
        print(f"Failed to play sound: {e}")

def save_game(player, world):
    """Save the current game state"""
    try:
        save_data = {
            "player": {
                "name": player.name,
                "health": player.health,
                "max_health": player.max_health,
                "attack": player.attack,
                "level": player.level,
                "exp": player.exp,
                "exp_to_next_level": player.exp_to_next_level,
                "mp": player.mp,  # Save current MP
                "max_mp": player.max_mp,  # Save max MP
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
        
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f)
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def load_game():
    """Load the game state from a file"""
    try:
        if not os.path.exists(SAVE_FILE):
            return None
            
        with open(SAVE_FILE, "r") as f:
            save_data = json.load(f)
        return save_data
    except Exception as e:
        print(f"Error loading game: {e}")
        return None 