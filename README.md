# Automated Colony Simulation

An automated Pygame colony simulation where autonomous villagers explore, remember resources, share knowledge, gather supplies, build shelters, and try to survive without direct player commands.

The project is designed as an emergent colony screensaver and as a playground for agentic simulation systems.

v0.5.0, Colony Roles and Production, turns the prototype survival sandbox into an early settlement simulator. Villagers now found a central village, take on lightweight roles, build around a settlement hub, use visible stockpiles and a workshop, coordinate shared targets through soft reservations, and gradually create farms when food pressure rises.

## Current Features

- Modular Python package under `src/`
- Rule-based terrain generation with grass, forest, plain, hill, wetland, dry, water, mountain, and shelter tiles
- Centralized world-generation settings and presets for reproducible/tunable worlds
- Generated world identity with title, subtitle, survival outlook, and hidden tags
- Larger explorable world with a camera-controlled map viewport
- 20-day Spring, Summer, Autumn, and Winter seasons that affect food and wood regrowth
- Seasonal terrain colors with final-day blending so the map visibly shifts across the year
- Terrain-based resource ecology with growth caps and gradual seasonal die-off
- Rare drought and heavy rain events that visibly tint terrain and mildly affect resource ecology
- Persistent world history for major environmental events
- Ambient wildlife with biome-suitable rabbits, deer, boar, and waterfowl
- Autonomous villagers with hunger, thirst, fatigue, carried food, and carried wood
- Lightweight villager roles: Generalist, Forager, Builder, and Scout
- Distinct role-based villager colors for at-a-glance readability
- Goal-based behavior for drinking, eating, sleeping, gathering, building, depositing, and exploring
- BFS pathfinding with occupied-tile avoidance
- Stuck recovery when paths collide or become blocked
- Personal agent memory for visible food, water, wood, and shelters
- Shared colony memory so discoveries can benefit other villagers
- Central settlement founding near the map center with clustered villager startup
- Settlement center and village hub behavior
- Physical food and wood stockpiles near the settlement
- Simple workshop that turns stored wood into building materials
- Clustered building placement near the village hub
- Local resource use radius with survival overrides
- Settlement needs / expanded building priorities
- Resource Reservation v1 for shared food, wood, build-site, and workshop targets
- Farming v1 with autonomous 2x2 farm plots driven by food pressure
- Settlement carrying-capacity and pressure status reporting as a measurement only, not a hard population cap
- Abstract colony storage for shared food and wood
- Selected-agent and selected-tile inspection UI with detailed internals
- Compact player-facing right-side status panel with world identity, time/season, colony status, active events, selection, history, legend, controls, and recent events
- Automated tests for pathfinding, memory, goals, building priorities, storage, reservations, farming, carrying capacity, movement recovery, world logic, and renderer selection helpers

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

World-generation settings are currently internal and preset-driven. The player-facing experience remains hands-off: launch the simulation, discover the generated world identity, and watch the colony.

Code and tests can create worlds with explicit settings:

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

No setup screen, sliders, dropdowns, or player-facing configuration UI is currently planned.

## Project Structure

- `src/main.py` - Pygame application loop
- `src/world.py` - World state, ticking, terrain, agents, shared systems
- `src/worldgen_settings.py` - Validated world-generation settings and presets
- `src/world_identity.py` - Generated world titles, subtitles, survival outlooks, and tags
- `src/agent.py` - Agent state, needs, memory scanning, goal selection
- `src/roles.py` - Lightweight role definitions and goal preference modifiers
- `src/actions.py` - Low-level executable actions
- `src/goals.py` - High-level goal selection layer
- `src/pathfinding.py` - BFS pathfinding
- `src/colony_memory.py` - Shared resource knowledge
- `src/colony_storage.py` - Abstract shared food and wood storage
- `src/settlement.py` - Settlement center, needs, farms, resource radius, and status tracking
- `src/stockpile.py` - Physical food and wood stockpile markers
- `src/workshop.py` - Simple workshop and building-material production
- `src/building_priorities.py` - Settlement construction priority rules
- `src/building_placement.py` - Bounded autonomous building placement helpers
- `src/reservations.py` - Lightweight shared-target reservation manager
- `src/farming.py` - 2x2 farm plots, placement, growth, and harvest helpers
- `src/carrying_capacity.py` - Measurement-only settlement pressure report
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

v0.5.0 completed the Colony Roles and Production milestone. The simulation now starts as a founded village, uses role preferences rather than player-assigned jobs, coordinates shared targets through Resource Reservation v1, and supports visible stockpiles, workshop production, autonomous farms, clustered building placement, settlement needs, and carrying-capacity status reporting.

Carrying capacity is a status and health estimate only. It is not a hard population maximum, and the UI intentionally avoids current/max population wording.

Full hauling/job assignment, migration, new settlements, reproduction/social simulation, roads, deeper agriculture, and Mysteries and Wanderers remain future work.

v0.3.0 completed the colony foundation: villagers can use personal and shared knowledge, recover from blocked movement, coordinate around shelter needs, and use simple shared storage.
