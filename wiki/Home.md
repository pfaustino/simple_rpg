# Simple RPG — Architecture (full scope)

Standalone Pygame roguelike — click-to-move exploration with turn-based combat. Minimal dependencies.

## Stack

Python 3, Pygame 2.5+. Single dependency in `requirements.txt`.

## Entry

`main.py` → `game.game.Game` → `run()`

## Layout

```
main.py
game/
  game.py       # Orchestrator, combat, inventory
  world.py      # Procedural world, viewport, click movement
  sprites.py    # SpriteSheet, animations
  combat.py     # CombatSystem
  spells.py
entities/
  character.py  # Stats, XP, equipment
  items.py      # Inventory
ui/
  console.py, bar.py, systemmenu.py, sprite_debug_window.py
utils/
  constants.py, helpers.py  # save/load, sounds
```

## Game loops (nested)

1. **Outer** `Game.run()` — exploration vs combat branches  
2. **Inner** `handle_movement()` — rAF-style poll: draw → events → click-to-move → random encounter  

Combat: menu turns (Attack / Strong Attack / Heal / Flee) with `time.sleep(0.1)` pacing.

## World

`World.generate_world()` — procedural tiles (grass/dirt/sand/water), trees/rocks overlays. Viewport 600×600 (10×10 cells × 60px). Resizable window.

## Persistence

`utils.helpers` → `player_save.json` (stats, position, inventory, equipment).

## Assets

`sprite_config.json` + Shikashi fantasy icon pack in `assets/`.

## Docs

`docs/adr/`.
