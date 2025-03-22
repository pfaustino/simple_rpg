import pygame
import random
from utils.constants import (
    WHITE, BLACK, RED, GREEN, BLUE, YELLOW,
    SOUND_ATTACK, SOUND_HIT, SOUND_MISS, SOUND_DEATH,
    SOUND_VICTORY, SOUND_LEVEL_UP
)
from utils.helpers import play_sound
from game.sprites import sprite_manager
from entities.items import Inventory

class Character:
    def __init__(self, name, level=1, health=100, max_health=100, attack=10, defense=5, speed=5, mp=0, max_mp=0, color=BLUE, character_type='player'):
        print(f"Creating character: {name}")  # Debug print
        self.name = name
        self.level = level
        self.health = health
        self.max_health = max_health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.mp = mp
        self.max_mp = max_mp
        self.exp = 0
        self.exp_to_next_level = 100
        self.kills = {}
        self.inventory = Inventory()
        self.equipment = {
            'weapon': None,
            'armor': None,
            'accessory': None
        }
        self.special_moves = []
        self.status_effects = []
        self.monster_data = None  # Store monster data for enemies
        self.sprite = sprite_manager.get_sprite('characters', 0)  # Use basic sprite instead of animated
        self.known_spells = []  # List of spell IDs the character knows
        if self.sprite and self.sprite.image:
            # Scale the sprite's image to 32x32
            self.sprite.image = pygame.transform.scale(self.sprite.image, (32, 32))
            self.sprite.rect = self.sprite.image.get_rect()  # Update rect to match new size
        self.color = color
        self.character_type = character_type

    def draw(self, screen, x, y):
        """Draw the character's sprite"""
        if self.sprite:
            screen.blit(self.sprite.image, (x, y))
        else:
            pygame.draw.rect(screen, self.color, (x, y, 32, 32))

    def is_alive(self):
        """Check if character is still alive"""
        return self.health > 0

    def get_total_attack(self):
        """Get total attack including equipment bonuses"""
        total = self.attack
        if self.equipment['weapon']:
            total += self.equipment['weapon'].get_bonus("attack", 0)
        return total

    def get_total_defense(self):
        """Get total defense including equipment bonuses"""
        total = self.defense
        if self.equipment['armor']:
            total += self.equipment['armor'].get_bonus("defense", 0)
        return total

    def take_damage(self, damage):
        """Take damage and update health"""
        reduced_damage = max(1, damage - self.get_total_defense())
        self.health = max(0, self.health - reduced_damage)
        play_sound(SOUND_ATTACK)
        return reduced_damage

    def attack_target(self, target):
        """Perform a basic attack with random damage variation"""
        base_damage = self.get_total_attack()
        # Roll 1d6 for damage variation (-3 to +3)
        damage_variation = random.randint(-3, 3)
        damage = max(1, base_damage + damage_variation)
        actual_damage = target.take_damage(damage)
        play_sound(SOUND_ATTACK)
        return actual_damage

    def strong_attack(self, target):
        """Perform a strong attack with random damage variation"""
        base_damage = self.get_total_attack() * 2
        # Roll 1d8 for damage variation (-4 to +4)
        damage_variation = random.randint(-4, 4)
        damage = max(1, base_damage + damage_variation)
        actual_damage = target.take_damage(damage)
        play_sound(SOUND_ATTACK)
        return actual_damage

    def heal(self, amount=None):
        """Heal the character with random variation or specified amount"""
        if amount is None:
            base_heal = 20
            # Roll 1d6 for healing variation (-3 to +3)
            heal_variation = random.randint(-3, 3)
            amount = max(1, base_heal + heal_variation)
            play_sound(SOUND_ATTACK)
        
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + amount)
            return amount
        return 0

    def level_up(self):
        """Level up the character"""
        self.level += 1
        self.exp -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        
        # Increase stats
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        self.defense += 1
        self.speed += 1
        self.max_mp += 5
        self.mp = self.max_mp
        play_sound(SOUND_LEVEL_UP)

    def equip_item(self, item):
        """Equip an item"""
        if item.item_type in self.equipment:
            # Store the currently equipped item
            old_item = self.equipment[item.item_type]
            
            # Remove old item's bonus if it exists
            if old_item:
                if item.item_type == "weapon":
                    self.attack -= old_item.get_bonus("attack", 0)
                elif item.item_type == "armor":
                    self.defense -= old_item.get_bonus("defense", 0)
            
            # Equip the new item
            self.equipment[item.item_type] = item
            
            # Apply new item's bonus
            if item.item_type == "weapon":
                self.attack += item.get_bonus("attack", 0)
            elif item.item_type == "armor":
                self.defense += item.get_bonus("defense", 0)
            
            # Return the old item if there was one
            return old_item
        return None

    def unequip_item(self, slot):
        """Unequip an item from a slot"""
        if slot in self.equipment and self.equipment[slot]:
            item = self.equipment[slot]
            
            # Remove item's bonus
            if item.item_type == "weapon":
                self.attack -= item.get_bonus("attack", 0)
            elif item.item_type == "armor":
                self.defense -= item.get_bonus("defense", 0)
            
            # Remove item from equipment
            self.equipment[slot] = None
            return item
        return None

    def gain_exp(self, amount):
        """Gain experience points and level up if possible"""
        self.exp += amount
        while self.exp >= self.exp_to_next_level:
            self.level_up()
    
    def record_kill(self, enemy_name):
        """Record a kill for a specific enemy type"""
        self.kills[enemy_name] = self.kills.get(enemy_name, 0) + 1
    
    def get_special_moves(self):
        """Get available special moves"""
        if self.character_type == 'enemy' and self.monster_data:
            return self.monster_data['special_moves']
        return self.special_moves

    def can_use_special_move(self, move):
        """Check if the character can use a special move"""
        return self.mp >= move['mp_cost']

    def use_special_move(self, move):
        """Use a special move and consume MP"""
        if self.can_use_special_move(move):
            self.mp -= move['mp_cost']
            return True
        return False

    def add_status_effect(self, effect):
        """Add a status effect to the character"""
        self.status_effects.append(effect)

    def remove_status_effect(self, effect):
        """Remove a status effect from the character"""
        if effect in self.status_effects:
            self.status_effects.remove(effect)

    def update_status_effects(self):
        """Update and remove expired status effects"""
        self.status_effects = [effect for effect in self.status_effects if not effect.is_expired()]
        for effect in self.status_effects:
            effect.apply(self)

    def can_cast_spell(self, spell_id, game):
        """Check if character can cast a spell"""
        if spell_id not in self.known_spells:
            return False, "Don't know this spell"
        return game.spell_system.can_cast_spell(self, spell_id)
    
    def cast_spell(self, target, spell_id, game):
        """Cast a spell on a target"""
        if spell_id not in self.known_spells:
            return False, "Don't know this spell"
        return game.spell_system.cast_spell(self, target, spell_id)
    
    def learn_spell(self, spell_id):
        """Learn a new spell"""
        if spell_id not in self.known_spells:
            self.known_spells.append(spell_id)
            return True, f"Learned new spell: {spell_id}"
        return False, "Already know this spell"
    
    def get_available_spells(self, game):
        """Get list of spells available to the character"""
        return game.spell_system.get_available_spells(self) 