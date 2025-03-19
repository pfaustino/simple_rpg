import pygame
import random
import time
from utils.constants import BLUE
from utils.helpers import play_sound
from utils.constants import (
    SOUND_LEVEL_UP, SOUND_HEAL, SOUND_STRONG_ATTACK,
    SOUND_ATTACK, SOUND_EQUIP
)
from entities.items import Inventory
from game.sprites import sprite_manager

class Character:
    def __init__(self, name, health=100, attack=10, color=BLUE, character_type='player'):
        print(f"Creating character: {name}")  # Debug print
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.level = 1
        self.exp = 0
        self.color = color
        self.character_type = character_type
        self.kills = {}
        self.inventory = Inventory()
        self.equipment = {
            "weapon": None,
            "armor": None
        }
        
        # Create animated sprite for the character
        self.sprite = sprite_manager.get_animated_sprite('characters', character_type, 'idle')
        self.current_animation = 'idle'
        self.direction = 0  # 0: right, 1: left, 2: up, 3: down
    
    def update(self):
        """Update the character's sprite animation"""
        if self.sprite:
            self.sprite.update()
    
    def set_animation(self, animation_type):
        """Change the character's animation"""
        if self.current_animation != animation_type:
            self.current_animation = animation_type
            self.sprite = sprite_manager.get_animated_sprite('characters', self.character_type, animation_type)
            self.sprite.set_direction(self.direction)
    
    def set_direction(self, direction):
        """Set the character's direction"""
        if self.direction != direction:
            self.direction = direction
            if self.sprite:
                self.sprite.set_direction(direction)
    
    def draw(self, screen, x, y):
        """Draw the character's sprite"""
        if self.sprite:
            self.sprite.rect.x = x
            self.sprite.rect.y = y
            screen.blit(self.sprite.image, self.sprite.rect)
    
    def is_alive(self):
        """Check if character is still alive"""
        return self.health > 0
    
    def get_total_attack(self):
        """Get total attack including equipment bonuses"""
        base_attack = self.attack
        if self.equipment["weapon"]:
            base_attack += self.equipment["weapon"].stats.get("attack", 0)
        return base_attack
    
    def get_total_defense(self):
        """Get total defense from equipment"""
        base_defense = 0
        if self.equipment["armor"]:
            base_defense += self.equipment["armor"].stats.get("defense", 0)
        return base_defense
    
    def take_damage(self, damage):
        # Apply defense reduction
        reduced_damage = max(1, damage - self.get_total_defense())
        self.health -= reduced_damage
        if self.health < 0:
            self.health = 0
        self.set_animation('hurt')
        play_sound(SOUND_ATTACK)  # Play sound when taking damage
        return reduced_damage
    
    def attack_target(self, target):
        self.set_animation('attack')
        damage = self.get_total_attack()
        target.take_damage(damage)
        play_sound(SOUND_ATTACK)
        return damage
    
    def strong_attack(self, target):
        self.set_animation('attack')
        damage = self.get_total_attack() * 2
        target.take_damage(damage)
        play_sound(SOUND_STRONG_ATTACK)
        return damage
    
    def heal(self):
        heal_amount = 20
        if self.health + heal_amount > self.max_health:
            heal_amount = self.max_health - self.health
        self.health += heal_amount
        play_sound(SOUND_HEAL)
        return heal_amount
    
    def gain_exp(self, amount):
        self.exp += amount
        while self.exp >= self.level * 100:
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.exp -= (self.level - 1) * 100
        self.max_health += 20
        self.health = self.max_health
        self.attack += 5
        print(f"{self.name} leveled up to level {self.level}!")
        # Play level up sound sequence
        play_sound(SOUND_LEVEL_UP, 200)
        time.sleep(0.1)
        play_sound(SOUND_LEVEL_UP + 200, 200)
    
    def record_kill(self, enemy_name):
        """Record a kill for a specific enemy type"""
        self.kills[enemy_name] = self.kills.get(enemy_name, 0) + 1
    
    def equip_item(self, item_index):
        """Equip an item from inventory"""
        if 0 <= item_index < len(self.inventory.items):
            item = self.inventory.items[item_index]
            if item.item_type in ["weapon", "armor"]:
                # Unequip current item if any
                if self.equipment[item.item_type]:
                    self.inventory.add_item(self.equipment[item.item_type])
                
                # Equip new item
                self.equipment[item.item_type] = item
                self.inventory.items.pop(item_index)
                return True
        return False
    
    def unequip_item(self, slot):
        """Unequip an item from a slot"""
        if self.equipment[slot]:
            if self.inventory.add_item(self.equipment[slot]):
                self.equipment[slot] = None
                return True
        return False 