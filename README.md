# Automated Colony Simulation

An automated Pygame colony simulation where autonomous villagers explore, remember resources, share knowledge, gather supplies, build shelters, and try to survive without direct player commands.

The project is designed as an emergent colony screensaver and as a playground for agentic simulation systems.

## Current Features

- Modular Python package under `src/`
- Rule-based terrain generation with grass, forest, plain, hill, wetland, dry, water, mountain, and shelter tiles
- Centralized world-generation settings and presets for reproducible/tunable worlds
- Larger explorable world with a camera-controlled map viewport
- 20-day Spring, Summer, Autumn, and Winter seasons that affect food and wood regrowth
- Seasonal terrain colors with final-day blending so the map visibly shifts across the year
- Terrain-based resource ecology with growth caps and gradual seasonal die-off
- Rare drought and heavy rain events that visibly tint terrain and mildly affect resource ecology
- Persistent world history for major environmental events
- Ambient wildlife with biome-suitable rabbits, deer, boar, and waterfowl
- Autonomous villagers with hunger, thirst, fatigue, carried food, and carried wood
- Goal-based behavior for drinking, eating, sleeping, gathering, building, depositing, and exploring
- BFS pathfinding with occupied-tile avoidance
- Stuck recovery when paths collide or become blocked
- Personal agent memory for visible food, water, wood, and shelters
- Shared colony memory so discoveries can benefit other villagers
- Shelter capacity and building-priority logic
- Abstract colony storage for shared food and wood
- Selected-agent and selected-tile inspection UI
- Readable right-side status panel with side-by-side simulation/colony data, active events, selection, history, legend, controls, and recent events
- Automated tests for pathfinding, memory, goals, building priorities, storage, movement recovery, world logic, and renderer selection helpers

## Controls

- `SPACE` - Pause or unpause
- `W`, `A`, `S`, `D` - Pan the camera
- `UP` - Increase simulation speed
- `DOWN` - Decrease simulation speed
- `R` - Restart the world
- `ESC` - Quit
- Left click an agent - Inspect that villager
- Left click an empty tile - Inspect that tile

## Installation

Requires Python 3.10+ and Pygame.

```bash
pip install pygame pytest
```

## Running

Run the current modular simulation:

```bash
python -m src.main
```

Run the automated test suite:

```bash
python -m pytest
```

The original single-file prototype is still present as `automated_colony_v0_1.py` for historical reference.

## World Generation Settings

Worlds can be created with explicit settings:

```python
from src.world import create_world
from src.worldgen_settings import WORLD_PRESETS, WorldGenSettings

world = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=42))

custom_world = create_world(settings=WorldGenSettings(
    seed=42,
    width=100,
    height=60,
    water_level=0.34,
    forest_density=0.70,
    climate_harshness=0.25,
))
```

Core setting ranges:
- `seed`: integer or `None`
- `width`, `height`: corrected to at least `1`
- `water_level`: `0.0` to `1.0`
- `forest_density`: `0.0` to `1.0`
- `climate_harshness`: `0.0` to `1.0`

Presets:
- `normal`: current default behavior
- `wet`: more water and wetter terrain
- `dry`: less water and more dry terrain
- `forest`: more forest coverage
- `harsh`: fewer resources, less wildlife, and more ecological pressure

## Project Structure

- `src/main.py` - Pygame application loop
- `src/world.py` - World state, ticking, terrain, agents, shared systems
- `src/worldgen_settings.py` - Validated world-generation settings and presets
- `src/agent.py` - Agent state, needs, memory scanning, goal selection
- `src/actions.py` - Low-level executable actions
- `src/goals.py` - High-level goal selection layer
- `src/pathfinding.py` - BFS pathfinding
- `src/colony_memory.py` - Shared resource knowledge
- `src/colony_storage.py` - Abstract shared food and wood storage
- `src/building_priorities.py` - Construction priority rules
- `src/resource_ecology.py` - Terrain and season based resource growth, caps, and die-off
- `src/environment_events.py` - Temporary drought and heavy rain events
- `src/world_history.py` - Persistent structured history entries for major events
- `src/wildlife.py` - Ambient biome-based wildlife spawning and wandering
- `src/seasons.py` - Season cycle and terrain-aware regrowth rules
- `src/renderer.py` - Pygame rendering and inspection UI
- `tests/` - Pytest coverage for core systems
- `ROADMAP.md` - Milestone roadmap
- `TASKS.md` - Task tracker
- `CHANGELOG.md` - Release notes

## Current Milestone

v0.4 is focused on a smarter world: deterministic rule-based terrain generation, larger explorable maps, rivers, terrain variety, and seasonal resource pressure.

v0.3.0 completed the colony foundation: villagers can use personal and shared knowledge, recover from blocked movement, coordinate around shelter needs, and use simple shared storage.
