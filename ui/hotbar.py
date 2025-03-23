# ui/hotbar.py

import pygame
from utils.constants import WHITE, BLACK

class Hotbar:
    def __init__(self, screen_width, screen_height, game):
        self.slots = [None] * 10  # 10 slots for actions
        self.slot_width = screen_width // 10  # Divide the screen width by the number of slots
        self.height = 40  # Height of the hotbar
        self.y_position = screen_height - self.height - 150  # Position above the console
        self.game = game  # Store the reference to the Game instance

    def set_action(self, slot_index, action):
        """Set an action for a specific slot."""
        if 0 <= slot_index < len(self.slots):
            self.slots[slot_index] = action

    def draw(self, screen):
        """Draw the hotbar on the screen."""
        # Draw the background for the hotbar
        pygame.draw.rect(screen, BLACK, (0, self.y_position, screen.get_width(), self.height))
        
        # Draw each slot
        for i in range(len(self.slots)):
            slot_x = i * self.slot_width
            pygame.draw.rect(screen, WHITE, (slot_x, self.y_position, self.slot_width, self.height), 1)  # Draw slot border
            
            # Draw action text if there is an action set
            if self.slots[i] is not None:
                action_text = self.slots[i]
                font = pygame.font.Font(None, 24)
                text_surface = font.render(action_text, True, WHITE)
                text_rect = text_surface.get_rect(center=(slot_x + self.slot_width // 2, self.y_position + self.height // 2))
                screen.blit(text_surface, text_rect)

    def handle_input(self, event):
        """Handle input for the hotbar."""
        if event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_0:  # Check for number keys 1-0
                slot_index = event.key - pygame.K_1 if event.key != pygame.K_0 else 9  # Adjust for 0 key
                if self.slots[slot_index] is not None:
                    # Execute the action associated with the slot
                    action = self.slots[slot_index]
                    self.execute_action(action)  # Call the method to execute the action
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
            mouse_x, mouse_y = event.pos
            if self.y_position <= mouse_y <= self.y_position + self.height:
                # Determine which slot was clicked
                slot_index = mouse_x // self.slot_width
                if 0 <= slot_index < len(self.slots):
                    action = self.slots[slot_index]
                    if action is not None:
                        # Execute the action associated with the slot
                        self.execute_action(action)  # Call the method to execute the action

    def execute_action(self, action):
        """Execute the action associated with the hotbar slot."""
        if action == "Attack":
            result = self.game.combat_system.handle_combat_action("Attack")
            print("Performing Attack")  # Replace with actual attack logic
        elif action == "Strong Attack":
            result = self.game.combat_system.handle_combat_action("Strong Attack")
            print("Performing Strong Attack")  # Replace with actual strong attack logic
        elif action == "Heal":
            result = self.game.combat_system.handle_combat_action("Heal")
            print("Performing Heal")  # Replace with actual heal logic

