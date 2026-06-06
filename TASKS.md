# Tasks

## Active


### TASK-2
Title: Refactor Single-File Prototype

Owner: Architect Agent

Status: Pending Verification

Description:
Split the single-file Pygame prototype `automated_colony_v0_1.py` into a modular package structure under `src/` to support future development.

Expected Output:
A clean, modularized structure under `src/` where imports are clear, constants live in a config file, and simulation code is separate from rendering.

Target Structure:
```text
src/
  main.py
  config.py
  tile.py
  world.py
  agent.py
  actions.py
  renderer.py
```

Acceptance Criteria:
- The game launches and runs exactly as before.
- No gameplay or behavior changes are introduced in this step.
- All import statements are clean and resolve correctly without circular dependencies.
- Magic numbers and simulation constants are moved to `src/config.py`.
- The rendering system does not contain or control simulation update logic.

Dependencies:
- TASK-1

Notes:
- This is a pure refactoring task. Do not add new gameplay features or assets.

---

### TASK-4
Title: Add Agent Memory

Owner: Gameplay Agent

Status: Pending Verification

Description:
Give agents a memory structure that allows them to scan nearby tiles (within their vision range) and remember resource locations (food, wood, water, shelters) for future use.

Expected Output:
Memory attributes added to the agent model with scan and update logic.

Acceptance Criteria:
- Agents scan surroundings at regular intervals or during updates.
- Memory tracks coordinate locations of visible water, food, wood, and shelters.
- Depleted or invalid resource memories are removed when an agent arrives and sees the resource is gone.
- Memory data is inspectable/accessible for future display in the UI.

Dependencies:
- TASK-2

Notes:
- Agents should not have omniscient knowledge of the entire map; they must explore to populate their memories.

---

## Backlog

### TASK-3
Title: Add BFS Pathfinding

Owner: Gameplay Agent

Status: Backlog

Description:
Implement a generic Breadth-First Search (BFS) pathfinding system that agents can use to find the shortest path to target tiles.

Expected Output:
A dedicated pathfinding utility module that computes valid coordinate paths avoiding obstacles.

Acceptance Criteria:
- A `find_path(world, start, destination)` function is created in a separate system module (e.g., `src/systems/pathfinding.py` or similar).
- Computed paths avoid water and mountain tiles.
- The pathfinder returns an empty path if the destination is unreachable.
- Path selection handles out-of-bounds inputs safely.

Dependencies:
- TASK-2

Notes:
- Agents should not run the pathfinding code internally; they should query the system.

---

### TASK-5
Title: Add Goal-Based Behavior

Owner: Gameplay Agent

Status: Backlog

Description:
Replace the current purely reactive action selection with a utility-scored, goal-based decision model.

Expected Output:
A goal system where agents evaluate and choose high-level goals (Drink, Eat, Sleep, Gather, Explore) based on needs.

Acceptance Criteria:
- Thirsty agents prioritize finding and moving toward water.
- Hungry agents prioritize finding and moving toward food.
- Tired agents prioritize finding and moving toward shelter.
- Agents default to exploration when needs are stable and they have no active tasks.
- Agents survive significantly longer on average compared to v0.1.

Dependencies:
- TASK-4

Notes:
- Use simple utility scoring to resolve competing goals.

---

### TASK-6
Title: Add Selected-Agent UI

Owner: Renderer Agent

Status: Backlog

Description:
Implement interactive clicking in Pygame to select and inspect a specific agent's status, needs, inventory, goals, and targets.

Expected Output:
An inspection panel in the UI rendering selected agent details, along with a visual highlight on the selected agent.

Acceptance Criteria:
- Clicking a tile with an agent selects that agent.
- Clicking an empty tile shows tile information instead.
- The side panel renders the selected agent's name, needs (hunger, thirst, fatigue), inventory, current action, and active goal/target.
- The selected agent is visually highlighted on the grid (e.g., with a border).
- Restarting the world or agent death resets selection state safely without crashing.

Dependencies:
- TASK-2
- TASK-5

Notes:
- Selection is read-only and must not influence agent behavior or alter simulation state.

---

### TASK-7
Title: Add Basic Tests

Owner: Tester Agent

Status: Backlog

Description:
Write a suite of automated unit tests covering key simulation subsystems such as world coordinate logic, pathfinding, agent memory, and goal utility selection.

Expected Output:
Automated test scripts using `pytest`.

Acceptance Criteria:
- Tests run successfully using the command `pytest`.
- Tests verify pathfinding logic on simple mock worlds (e.g., finding paths, obstacle avoidance, unreachable targets).
- Tests verify world boundary checking and tile walkability.
- Tests verify agent memory updates (adding and removing resource coordinates).
- Tests verify basic goal priority scoring (e.g., high thirst leads to water goal).

Dependencies:
- TASK-2
- TASK-3
- TASK-4
- TASK-5

Notes:
- Use fixed seeds and mock grids in tests to avoid randomness issues.

---

## Completed

### TASK-1
Title: Create Project Documents

Owner: Docs Agent

Status: Completed

Description:
Establish the base project documentation to guide development and keep agents and humans aligned. This includes creating and verifying README.md, DESIGN.md, ROADMAP.md, and TASKS.md.

Expected Output:
Completed core project documentation files in the repository root.

Acceptance Criteria:
- README.md exists and explains the project concept and run instructions.
- DESIGN.md exists and explains the core simulation loop and design priorities.
- ROADMAP.md exists and outlines milestones from v0.1 to v0.5.
- TASKS.md exists and outlines the active tasks and backlog for v0.2.

Dependencies:
- None

Notes:
- Completed during initial planning phase.
