import pygame
import random 
from utils.helpers import play_sound, play_wave_sound
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, BLUE,
    SOUND_ATTACK, SOUND_HIT, SOUND_MISS, SOUND_DEATH,
    SOUND_VICTORY, SOUND_COMBAT_START, SOUND_COMBAT_END,
    WINDOW_SIZE, YELLOW, SOUND_HEAL
)
from entities.character import Character
from ui.bar import Bar
from ui.console import MessageConsole

class CombatSystem:
    def __init__(self, game):
        self.game = game
        self.world = game.world  # Add world reference
        self.in_combat = False
        self.current_enemy = None
        self.selected_option = 0
        self.combat_options = ["Attack", "Strong Attack", "Heal", "Flee"]
        self.combat_animation_frame = 0

    def start_combat(self, enemy):
        """Start a new combat encounter"""
        self.in_combat = True
        self.current_enemy = enemy
        self.selected_option = 0
        
        # Add initial combat message
        self.game.message_console.add_message(f"Combat started with {enemy.name}!")
        
        # Stop any currently playing sounds and play combat start sound
        try:
            pygame.mixer.stop()  # Stop all currently playing sounds
            pygame.mixer.music.stop()  # Stop any playing music
            pygame.mixer.music.unload()  # Unload any loaded music
            play_wave_sound(SOUND_COMBAT_START)
        except Exception as e:
            print(f"Failed to play combat sound: {e}")

    def end_combat(self):
        """End the current combat encounter"""
        self.in_combat = False
        self.current_enemy = None
        self.selected_option = 0
        
        # Stop combat music
        try:
            pygame.mixer.stop()
        except Exception as e:
            print(f"Failed to stop combat sound: {e}")

    def handle_combat_action(self, action):
        """Handle a combat action"""
        print(f"CombatSystem: Handling action: {action}")
        print(f"CombatSystem state - in_combat: {self.in_combat}, current_enemy: {self.current_enemy}")
        
        if not self.in_combat or not self.current_enemy:
            print("CombatSystem: Not in combat or no enemy - returning combat_end")
            return "combat_end"
        
        # Check if enemy is already defeated
        if self.current_enemy.health <= 0:
            print("CombatSystem: Enemy already defeated - ending combat")
            self.end_combat()
            return "combat_end"
        
        if action == "Attack":
            print("CombatSystem: Processing Attack action")
            damage = self.game.player.attack
            actual_damage = self.current_enemy.take_damage(damage)
            self.game.message_console.add_message(f"You deal {actual_damage} damage to {self.current_enemy.name}!")
            play_wave_sound(SOUND_ATTACK)
        
        elif action == "Strong Attack":
            print("CombatSystem: Processing Strong Attack action")
            if self.game.player.mp >= 10:  # Check if player has enough MP
                self.game.player.mp -= 10  # Consume MP
                damage = self.game.player.attack * 2  # Double damage
                actual_damage = self.current_enemy.take_damage(damage)
                self.game.message_console.add_message(f"You perform a strong attack for {actual_damage} damage!")
                play_wave_sound(SOUND_HIT)
            else:
                self.game.message_console.add_message("Not enough MP for strong attack!")
                play_wave_sound(SOUND_MISS)
                return "continue"
        
        elif action == "Heal":
            print("CombatSystem: Processing Heal action")
            if self.game.player.mp >= 20:  # Check if player has enough MP
                self.game.player.mp -= 20  # Consume MP
                heal_amount = 50
                self.game.player.heal(heal_amount)
                self.game.message_console.add_message(f"You heal for {heal_amount} HP!")
                play_wave_sound(SOUND_HEAL)
            else:
                self.game.message_console.add_message("Not enough MP to heal!")
                play_wave_sound(SOUND_MISS)
                return "continue"
        
        elif action == "Flee":
            print("CombatSystem: Processing Flee action")
            if random.random() < 0.5:  # 50% chance to flee
                self.game.message_console.add_message("You successfully flee!")
                play_wave_sound(SOUND_COMBAT_END)
                self.end_combat()
                return "combat_end"
            else:
                self.game.message_console.add_message("Failed to flee!")
                play_wave_sound(SOUND_MISS)

        # Check if enemy is defeated
        if self.current_enemy.health <= 0:
            print("CombatSystem: Enemy defeated")
            self.game.handle_enemy_defeat(self.current_enemy)
            play_wave_sound(SOUND_VICTORY)
            self.end_combat()
            return "combat_end"

        # Enemy's turn
        print("CombatSystem: Processing enemy turn")
        enemy_damage = self.current_enemy.attack
        self.game.player.take_damage(enemy_damage)
        self.game.message_console.add_message(f"{self.current_enemy.name} attacks for {enemy_damage} damage!")
        play_wave_sound(SOUND_ATTACK)

        # Check if player is defeated
        if self.game.player.health <= 0:
            print("CombatSystem: Player defeated")
            self.game.message_console.add_message("You have been defeated!")
            play_wave_sound(SOUND_DEATH)
            self.end_combat()
            return "game_over"

        # Regenerate MP
        self.game.player.mp = min(self.game.player.max_mp, self.game.player.mp + 2)
        if self.game.player.mp < self.game.player.max_mp:
            self.game.message_console.add_message("You recover 2 MP!")

        print("CombatSystem: Action completed successfully")
        return "continue"

    def draw_combat_screen(self):
        """Draw the combat screen"""
        # Draw the world viewport
        self.game.world.display_viewport(self.game.screen, self.game.world.player_x, self.game.world.player_y)
        
        # Draw the player character
        player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        self.game.player.draw(self.game.screen, player_screen_x, player_screen_y)
        
        # Draw the enemy if it exists
        if self.current_enemy:
            # Position enemy on the right side of the player
            enemy_screen_x = player_screen_x + 100  # 100 pixels to the right of player
            enemy_screen_y = player_screen_y
            self.current_enemy.draw(self.game.screen, enemy_screen_x, enemy_screen_y)
        
        # Draw combat UI elements
        # Draw player status bar at the top
        self.game.bar_renderer.draw_health_bar(self.game.screen, self.game.player, 10, 10)
        self.game.bar_renderer.draw_mp_bar(self.game.screen, self.game.player, 10, 35)
        self.game.bar_renderer.draw_xp_bar(self.game.screen, self.game.player, 10, 60)
        
        # Draw enemy health bar if enemy exists
        if self.current_enemy:
            self.game.bar_renderer.draw_health_bar(self.game.screen, self.current_enemy, 10, 85)
        
        # Draw combat options with number key shortcuts
        combat_options = [
            "1 - Attack",
            "2 - Strong Attack (10 MP)",
            "3 - Heal (20 MP)",
            "4 - Flee"
        ]
        for i, option in enumerate(combat_options):
            color = WHITE if i == self.selected_option else (200, 200, 200)
            text = self.game.font.render(option, True, color)
            self.game.screen.blit(text, (20, 120 + i * 30))
        
        # Draw message console at the bottom
        console_height = 150
        self.game.message_console.draw(self.game.screen, 0, SCREEN_HEIGHT - console_height, SCREEN_WIDTH, console_height)

    def update(self):
        """Update combat system state"""
        # Update any ongoing animations or effects
        self.combat_animation_frame = (self.combat_animation_frame + 1) % 60  # 60 frames per second