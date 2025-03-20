import pygame
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
        self.exp_to_next_level = 100
        self.color = color
        self.character_type = character_type
        self.kills = {}
        self.inventory = Inventory()
        self.equipment = {
            "weapon": None,
            "armor": None
        }
        self.sprite = sprite_manager.get_sprite('characters', 0)  # Use basic sprite instead of animated
        if self.sprite and self.sprite.image:
            # Scale the sprite's image to 32x32
            self.sprite.image = pygame.transform.scale(self.sprite.image, (32, 32))
            self.sprite.rect = self.sprite.image.get_rect()  # Update rect to match new size

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
        """Calculate total attack including equipment"""
        base_attack = self.attack
        if self.equipment["weapon"]:
            base_attack += self.equipment["weapon"].bonus
        return base_attack

    def get_total_defense(self):
        """Calculate total defense including equipment"""
        base_defense = 0
        if self.equipment["armor"]:
            base_defense += self.equipment["armor"].bonus
        return base_defense

    def take_damage(self, damage):
        """Take damage and update health"""
        reduced_damage = max(1, damage - self.get_total_defense())
        self.health = max(0, self.health - reduced_damage)
        play_sound(SOUND_ATTACK)
        return reduced_damage

    def attack_target(self, target):
        """Perform a basic attack"""
        damage = self.get_total_attack()
        target.take_damage(damage)
        play_sound(SOUND_ATTACK)
        return damage

    def strong_attack(self, target):
        """Perform a strong attack"""
        damage = self.get_total_attack() * 2
        target.take_damage(damage)
        play_sound(SOUND_STRONG_ATTACK)
        return damage

    def heal(self):
        """Heal the character"""
        heal_amount = 20
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + heal_amount)
            play_sound(SOUND_HEAL)
            return heal_amount
        return 0

    def level_up(self):
        """Level up the character"""
        self.level += 1
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        play_sound(SOUND_LEVEL_UP)

    def equip_item(self, item):
        """Equip an item"""
        if item.type in self.equipment:
            if self.equipment[item.type]:
                self.inventory.add_item(self.equipment[item.type])
            self.equipment[item.type] = item
            play_sound(SOUND_EQUIP)
            return True
        return False

    def gain_exp(self, amount):
        self.exp += amount
        while self.exp >= self.level * 100:
            self.level_up()
    
    def record_kill(self, enemy_name):
        """Record a kill for a specific enemy type"""
        self.kills[enemy_name] = self.kills.get(enemy_name, 0) + 1
    
    def unequip_item(self, slot):
        """Unequip an item from a slot"""
        if self.equipment[slot]:
            if self.inventory.add_item(self.equipment[slot]):
                self.equipment[slot] = None
                return True
        return False 