# Automated Colony Simulation

A world simulation where autonomous agents explore, gather resources, build shelters, cooperate, and survive in an emergent environment. The player does not directly command units, but instead generates the world and observes the emergent stories and history that unfold.

*Note: Built as an automated colony simulation to serve as a distracting screensaver and showcase agentic AI programming.*

## Current Features (v0.1)
- **Random World Generation**: Dynamic map generation featuring grass, forest, water, mountains, and shelters.
- **Autonomous Villagers**: Agents with individual needs (hunger, thirst, fatigue) that make survival-based decisions.
- **Resource Gathering**: Agents gather food and wood from the environment to survive and build.
- **Shelter Building & Sleep**: Villagers collect wood to build shelters and sleep to recover fatigue.
- **Event Log**: Live text updates logging meaningful world events.
- **Pygame Renderer**: Custom visual rendering utilizing ASCII-like symbols (`@`, `f`, `w`) and interactive side panel.

## Controls
- `SPACE` - Pause / Unpause simulation
- `UP` - Increase simulation speed (ticks per second)
- `DOWN` - Decrease simulation speed (ticks per second)
- `R` - Restart simulation (regenerates world and respawns agents)
- `ESC` - Quit simulation

## Installation
Requires Python 3.x and Pygame.

1. Install Pygame:
   ```bash
   pip install pygame
   ```

## Running
Run the single-file prototype:
```bash
python automated_colony_v0_1.py
```

## Project Structure
- [automated_colony_v0_1.py](file:///c:/Users/astro/Documents/Projects/Automated-Colony/automated_colony_v0_1.py): The single-file prototype simulation and renderer.
- [DESIGN.md](file:///c:/Users/astro/Documents/Projects/Automated-Colony/DESIGN.md): The core design vision, priorities, and survival rules.
- [ROADMAP.md](file:///c:/Users/astro/Documents/Projects/Automated-Colony/ROADMAP.md): Overview of developmental phases from v0.1 to v0.5.
- [TASKS.md](file:///c:/Users/astro/Documents/Projects/Automated-Colony/TASKS.md): The tracking sheet for active tasks and the backlog.
- [AGENTS/](file:///c:/Users/astro/Documents/Projects/Automated-Colony/AGENTS): Guideline markdown files defining specialist agent responsibilities.

## Future Plans (v0.2 - Intelligent Survival)
The next milestone focuses on enhancing agent decision-making:
- Refactoring the single-file prototype into modular Python files (`src/`).
- Introducing BFS pathfinding to replace random-walk movement.
- Implementing agent memory so villagers remember resource locations.
- Introducing utility-scored goal-based behavior.
- Adding interactive agent selection to inspect individual needs, inventory, and active goals.
