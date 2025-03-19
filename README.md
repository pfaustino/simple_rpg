# Simple RPG

A simple RPG game built with Python and Pygame, featuring procedurally generated worlds, dynamic terrain, and overlay systems.

## Features

- Procedurally generated world with varied terrain types (grass, dirt, sand, water)
- Dynamic overlay system for environmental objects (trees, rocks, bushes)
- Player movement and interaction
- Save/load game functionality
- Sprite debug viewer for development

## Requirements

- Python 3.8+
- Pygame 2.0+

For a complete list of dependencies, see `requirements.txt`.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/simple_rpg.git
cd simple_rpg
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

To start the game, run:
```bash
python main.py
```

## Project Structure

- `assets/` - Game assets (sprites, textures, etc.)
- `entities/` - Entity-related code (player, NPCs, etc.)
- `game/` - Core game mechanics and world generation
- `ui/` - User interface components
- `utils/` - Utility functions and helpers

## Development

The project uses a modular architecture with the following key components:

- World Generation System
- Sprite Management System
- Entity Component System
- Save/Load System

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Sprite assets from various sources (see sprite_config.json for details)
- Community contributions and feedback 