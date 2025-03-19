#!/usr/bin/env python3
"""Main entry point for the Simple RPG game."""

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.game import Game

def main():
    """Run the game."""
    game = Game()
    game.run()

if __name__ == "__main__":
    main() 