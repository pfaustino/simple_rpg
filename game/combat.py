import pygame
from utils.helpers import play_sound
from utils.constants import (
    SOUND_ATTACK, SOUND_STRONG_ATTACK, SOUND_HEAL, SOUND_FLEE,
    WINDOW_SIZE
)

class CombatSystem:
    def __init__(self, game):
        self.game = game
        self.message = ""
        self.message_time = 0
        self.message_duration = 3  # seconds
        self.last_player_damage = 0
        self.last_enemy_damage = 0
        self.combat_animation_frame = 0

    def handle_battle(self, enemy):
        """Handle one round of battle with an enemy"""
        self.game.message_console.add_message(f"A {enemy.name} appears!")
        self.game.current_enemy = enemy  # Set current enemy for drawing
        
        while self.game.in_combat:  # Combat loop - use game's combat state
            # Draw the combat screen every frame
            self.game.draw_combat_screen()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.game_running = False
                    self.game.in_combat = False  # Make sure to exit combat
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:  # Basic attack
                        damage = self.game.world.player.attack_target(enemy)
                        self.game.message_console.add_message(f"You hit {enemy.name} for {damage} damage!")
                        self.last_player_damage = damage
                        play_sound(SOUND_ATTACK)
                        
                        if not enemy.is_alive():
                            self.game.handle_enemy_defeat(enemy)
                            self.game.in_combat = False
                            self.game.current_enemy = None  # Clear current enemy
                            return False
                        
                        # Enemy's turn after player attacks
                        self.enemy_turn(enemy)
                        if not self.game.world.player.is_alive():
                            self.game.in_combat = False
                            return False
                        
                    elif event.key == pygame.K_2:  # Strong attack
                        damage = self.game.world.player.strong_attack(enemy)
                        self.game.message_console.add_message(f"You hit {enemy.name} HARD for {damage} damage!")
                        self.last_player_damage = damage
                        play_sound(SOUND_STRONG_ATTACK)
                        
                        if not enemy.is_alive():
                            self.game.handle_enemy_defeat(enemy)
                            self.game.in_combat = False
                            self.game.current_enemy = None  # Clear current enemy
                            return False
                        
                        # Enemy's turn after player attacks
                        self.enemy_turn(enemy)
                        if not self.game.world.player.is_alive():
                            self.game.in_combat = False
                            return False
                        
                    elif event.key == pygame.K_3:  # Heal
                        heal_amount = self.game.world.player.heal()
                        if heal_amount > 0:
                            self.game.message_console.add_message(f"You healed for {heal_amount} health!")
                            play_sound(SOUND_HEAL)
                        else:
                            self.game.message_console.add_message("You are already at full health!")
                        
                        # Enemy's turn after player heals
                        self.enemy_turn(enemy)
                        if not self.game.world.player.is_alive():
                            self.game.in_combat = False
                            return False
                        
                    elif event.key == pygame.K_4:  # Flee
                        play_sound(SOUND_FLEE)
                        if pygame.time.get_ticks() % 2 == 0:  # 50% chance to flee
                            self.game.message_console.add_message("You successfully fled from battle!")
                            self.game.in_combat = False
                            self.game.current_enemy = None  # Clear current enemy
                            return False
                        else:
                            self.game.message_console.add_message("Failed to flee!")
                            # Enemy's turn after failed flee
                            self.enemy_turn(enemy)
                            if not self.game.world.player.is_alive():
                                self.game.in_combat = False
                                return False
            
            # Cap the frame rate
            self.game.clock.tick(60)
        
        return False  # Combat is over

    def enemy_turn(self, enemy):
        """Handle enemy's turn in battle"""
        if enemy.health > 0:
            damage = enemy.attack_target(self.game.world.player)
            self.game.message_console.add_message(f"{enemy.name} hits you for {damage} damage!")
            self.last_enemy_damage = damage
            
            if not self.game.world.player.is_alive():
                self.game.message_console.add_message("You have been defeated!")
                self.game.show_game_over()
                self.game.game_running = False

    def draw_combat_message(self):
        """Draw the current combat message"""
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.message_time < self.message_duration:
            self.game.draw_text(self.message, 10, 420)