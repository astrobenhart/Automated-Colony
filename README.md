# Automated Colony Simulation

An automated Pygame colony simulation where autonomous villagers explore, remember resources, share knowledge, gather supplies, build shelters, and try to survive without direct player commands.

The project is designed as an emergent colony screensaver and as a playground for agentic simulation systems.

## Current Features

- Modular Python package under `src/`
- Random terrain generation with grass, forest, water, mountain, and shelter tiles
- Autonomous villagers with hunger, thirst, fatigue, carried food, and carried wood
- Goal-based behavior for drinking, eating, sleeping, gathering, building, depositing, and exploring
- BFS pathfinding with occupied-tile avoidance
- Stuck recovery when paths collide or become blocked
- Personal agent memory for visible food, water, wood, and shelters
- Shared colony memory so discoveries can benefit other villagers
- Shelter capacity and building-priority logic
- Abstract colony storage for shared food and wood
- Selected-agent and selected-tile inspection UI
- Readable right-side status panel with simulation, controls, colony, selection, and event sections
- Automated tests for pathfinding, memory, goals, building priorities, storage, movement recovery, world logic, and renderer selection helpers

## Controls

- `SPACE` - Pause or unpause
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

## Project Structure

- `src/main.py` - Pygame application loop
- `src/world.py` - World state, ticking, terrain, agents, shared systems
- `src/agent.py` - Agent state, needs, memory scanning, goal selection
- `src/actions.py` - Low-level executable actions
- `src/goals.py` - High-level goal selection layer
- `src/pathfinding.py` - BFS pathfinding
- `src/colony_memory.py` - Shared resource knowledge
- `src/colony_storage.py` - Abstract shared food and wood storage
- `src/building_priorities.py` - Construction priority rules
- `src/renderer.py` - Pygame rendering and inspection UI
- `tests/` - Pytest coverage for core systems
- `ROADMAP.md` - Milestone roadmap
- `TASKS.md` - Task tracker
- `CHANGELOG.md` - Release notes

## Current Milestone

v0.3.0 completes the colony foundation: villagers can use personal and shared knowledge, recover from blocked movement, coordinate around shelter needs, and use simple shared storage.

Next work is expected to focus on v0.4 world generation and longer-term colony systems.
