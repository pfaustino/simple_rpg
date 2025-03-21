import pygame
from utils.helpers import play_sound
from utils.constants import (
    SOUND_ATTACK, SOUND_STRONG_ATTACK, SOUND_HEAL, SOUND_FLEE,
    WINDOW_SIZE
)

class CombatSystem:
    def __init__(self, game):
        self.game = game
        self.in_combat = False
        self.current_enemy = None
        self.turn_order = []
        self.selected_option = 0
        self.combat_options = ["Attack", "Special Move", "Heal", "Flee"]
        self.special_moves = []  # Will be populated with player's special moves
        self.message = ""
        self.message_time = 0
        self.message_duration = 3  # seconds
        self.last_player_damage = 0
        self.last_enemy_damage = 0
        self.combat_animation_frame = 0

    def start_combat(self, enemy):
        """Start a new combat encounter"""
        self.in_combat = True
        self.current_enemy = enemy
        self.turn_order = self.determine_turn_order()
        self.selected_option = 0
        self.game.message_console.add_message(f"A {enemy.name} appears!")
        play_sound(SOUND_ENEMY_DEFEAT)

    def end_combat(self):
        """End the current combat encounter"""
        self.in_combat = False
        self.current_enemy = None
        self.turn_order = []
        self.selected_option = 0

    def determine_turn_order(self):
        """Determine the order of turns based on speed"""
        characters = [self.game.player, self.current_enemy]
        return sorted(characters, key=lambda x: x.speed, reverse=True)

    def handle_combat_turn(self, event):
        """Handle a single turn of combat"""
        if not self.in_combat:
            return "continue"

        # Update status effects
        for character in self.turn_order:
            character.update_status_effects()

        # Check if combat is over
        if not self.game.player.is_alive():
            return "game_over"
        if not self.current_enemy.is_alive():
            self.handle_enemy_defeat()
            return "continue"

        # Handle input for player's turn
        if self.turn_order[0] == self.game.player:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.combat_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.combat_options)
                elif event.key == pygame.K_RETURN:
                    return self.handle_player_action()
        else:
            # Enemy's turn
            return self.handle_enemy_turn()

        return "continue"

    def handle_player_action(self):
        """Handle the player's chosen action"""
        action = self.combat_options[self.selected_option]
        
        if action == "Attack":
            damage = self.game.player.attack
            actual_damage = self.current_enemy.take_damage(damage)
            self.game.message_console.add_message(f"You deal {actual_damage} damage to {self.current_enemy.name}!")
        
        elif action == "Special Move":
            special_moves = self.game.player.get_special_moves()
            if not special_moves:
                self.game.message_console.add_message("No special moves available!")
                return "continue"
            
            # For now, just use the first special move
            move = special_moves[0]
            if self.game.player.use_special_move(move):
                damage = move['damage']
                actual_damage = self.current_enemy.take_damage(damage)
                self.game.message_console.add_message(f"You use {move['name']} for {actual_damage} damage!")
                
                # Apply move effects
                if "effect" in move:
                    self.game.message_console.add_message(f"Effect: {move['effect']}")
            else:
                self.game.message_console.add_message("Not enough MP!")
                return "continue"
        
        elif action == "Heal":
            if self.game.player.inventory.has_item("Health Potion"):
                self.game.player.inventory.remove_item("Health Potion")
                heal_amount = 50
                self.game.player.heal(heal_amount)
                self.game.message_console.add_message(f"You heal for {heal_amount} HP!")
            else:
                self.game.message_console.add_message("No health potions!")
                return "continue"
        
        elif action == "Flee":
            if random.random() < 0.5:  # 50% chance to flee
                self.game.message_console.add_message("You successfully flee!")
                self.end_combat()
                return "continue"
            else:
                self.game.message_console.add_message("Failed to flee!")

        # Rotate turn order
        self.turn_order = self.turn_order[1:] + [self.turn_order[0]]
        return "continue"

    def handle_enemy_turn(self):
        """Handle the enemy's turn"""
        enemy = self.current_enemy
        
        # Get available special moves
        special_moves = enemy.get_special_moves()
        
        # Decide whether to use a special move (30% chance)
        if special_moves and random.random() < 0.3:
            move = random.choice(special_moves)
            if enemy.use_special_move(move):
                damage = move['damage']
                actual_damage = self.game.player.take_damage(damage)
                self.game.message_console.add_message(f"{enemy.name} uses {move['name']} for {actual_damage} damage!")
                
                # Apply move effects
                if "effect" in move:
                    self.game.message_console.add_message(f"Effect: {move['effect']}")
            else:
                # If can't use special move, do normal attack
                damage = enemy.attack
                actual_damage = self.game.player.take_damage(damage)
                self.game.message_console.add_message(f"{enemy.name} attacks for {actual_damage} damage!")
        else:
            # Normal attack
            damage = enemy.attack
            actual_damage = self.game.player.take_damage(damage)
            self.game.message_console.add_message(f"{enemy.name} attacks for {actual_damage} damage!")

        # Rotate turn order
        self.turn_order = self.turn_order[1:] + [self.turn_order[0]]
        return "continue"

    def handle_enemy_defeat(self):
        """Handle enemy defeat"""
        self.game.handle_enemy_defeat(self.current_enemy)
        self.end_combat()

    def draw_combat_screen(self):
        """Draw the combat screen"""
        # Draw the world viewport
        self.game.world.display_viewport(self.game.world.screen, self.game.world.player_x, self.game.world.player_y)
        
        # Draw combat UI
        self.draw_combat_ui()

    def draw_combat_ui(self):
        """Draw the combat UI elements"""
        # Draw health bars
        self.game.bar_renderer.draw_health_bar(self.game.screen, self.game.player, (20, 20))
        self.game.bar_renderer.draw_health_bar(self.game.screen, self.current_enemy, (20, 60))
        
        # Draw MP bars
        self.game.bar_renderer.draw_mp_bar(self.game.screen, self.game.player, (20, 40))
        if self.current_enemy.max_mp > 0:
            self.game.bar_renderer.draw_mp_bar(self.game.screen, self.current_enemy, (20, 80))
        
        # Draw combat options
        for i, option in enumerate(self.combat_options):
            color = YELLOW if i == self.selected_option else WHITE
            text = self.game.font.render(option, True, color)
            self.game.screen.blit(text, (20, 120 + i * 30))
        
        # Draw turn order
        turn_text = "Your turn" if self.turn_order[0] == self.game.player else f"{self.current_enemy.name}'s turn"
        text = self.game.font.render(turn_text, True, WHITE)
        self.game.screen.blit(text, (20, 220))

    def draw_combat_message(self):
        """Draw the current combat message"""
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.message_time < self.message_duration:
            self.game.draw_text(self.message, 10, 420)