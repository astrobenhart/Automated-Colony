# Tasks

## Active

No active task.

---

## Backlog

### TASK-24
Title: Roadmap Settlement Formation

Owner: Planner Agent

Status: Backlog

Description:
Use GitHub Issue #14 to plan settlement centers, village hubs, local resource radius, clustered building placement, expansion, migration, splinter settlements, and settlement identity.

Expected Output:
A staged implementation plan for evolving survival colonies into recognizable villages and historical settlements.

Acceptance Criteria:
- Settlement Center, Settlement Radius, Physical Stockpiles, Expansion/Migration, and Village Identity phases are scoped.
- v0.5/v0.6/v0.7 milestone placement is clear.
- Non-goals such as warfare, diplomacy, economy, politics, and kingdoms remain explicitly out of scope.
- No gameplay code is changed by the planning task.

Dependencies:
- TASK-23

Notes:
- Roadmap reference: Issue #14, Roadmap: Settlement and Village Formation Systems.

---

### TASK-12
Title: Design Staged Population Growth

Owner: Planner Agent

Status: Backlog

Description:
Design a staged path for population recovery and future reproduction, starting with migration before lifecycle and family systems.

Expected Output:
A design issue and implementation plan for migration, lifecycle, family relationships, and lineage/history integration.

Acceptance Criteria:
- Phase 1 migration/replenishment rules are defined.
- Later lifecycle, family, and lineage phases are scoped separately.
- Dependencies on food surplus, shelter capacity, storage or settlement center, and carrying capacity are documented.
- The design avoids scripted romance and hardcoded story events.

Dependencies:
- TASK-5
- TASK-8
- TASK-9
- TASK-11

Notes:
- This is a planning task only; do not implement reproduction until prerequisites are stable.

---

## Completed

### TASK-27
Title: Add Environmental World History

Owner: Gameplay/Worldgen Agent

Status: Completed

Description:
Implement GitHub Issue #17 by adding persistent structured world history for major environmental events.

Expected Output:
A long-term history store separate from the short-term event log, with environmental entries for drought and heavy rain beginnings/endings and future-ready categories for seasons, wildlife, and settlements.

Acceptance Criteria:
- World owns persistent history.
- History entries store day, year, season, category, title, and description.
- History supports recent entries, category filtering, and count.
- Drought and heavy rain start/end events are recorded in history and the existing event log.
- The right panel shows compact history information.
- Existing tests pass.

Dependencies:
- TASK-19
- TASK-25
- TASK-26

Notes:
- This is environmental history v1 only; no settlement history, migration history, ancestry, lineage, ruins, or myths were added.

---

### TASK-26
Title: Add Biome Wildlife

Owner: Gameplay/Worldgen Agent

Status: Completed

Description:
Implement GitHub Issue #16 by adding simple ambient wildlife that spawns from biome suitability.

Expected Output:
Visible, deterministic rabbits, deer, boar, and waterfowl that make the world feel alive without affecting villager goals, movement, hunting, combat, or survival balance.

Acceptance Criteria:
- Exactly four species exist: rabbit, deer, boar, and waterfowl.
- Wildlife spawns on suitable terrain and avoids water, mountains, and occupied villager tiles.
- Wildlife count respects a configured cap.
- Animals can idle and lightly wander without blocking villagers.
- Wildlife symbols render on the map and are represented in the legend.
- Existing tests pass.

Dependencies:
- TASK-17
- TASK-19
- TASK-23
- TASK-25

Notes:
- This is ambient wildlife v1 only; no hunting, combat, reproduction, domestication, predator/prey simulation, animal needs, or animal-driven resource use was added.

---

### TASK-25
Title: Add Basic Environmental Events

Owner: Gameplay/Worldgen Agent

Status: Completed

Description:
Implement GitHub Issue #15 by adding rare, visible, temporary drought and heavy rain events.

Expected Output:
Environmental events that are stored on the world, logged, visible on the map, and mildly affect resource ecology without causing catastrophic collapse.

Acceptance Criteria:
- Drought and heavy rain can start and expire.
- Event start/end messages are logged.
- Active events are stored on the world.
- Active events are visible or inspectable in the renderer.
- Events mildly influence resource growth or die-off.
- Permanent water and rivers remain water.
- Existing tests pass.

Dependencies:
- TASK-19
- TASK-23

Notes:
- Wildfire and flood remain future work.
- No wildlife, farming, roles, reproduction, particles, complex weather, or destructive water changes were added.

---

### TASK-23
Title: Add Biome Resource Ecology

Owner: Gameplay/Worldgen Agent

Status: Completed

Description:
Implement GitHub Issue #13 by making resource growth, caps, and gradual die-off depend on terrain and season.

Expected Output:
A table-driven ecology system where wetlands, forests, plains, hills, dry terrain, mountains, and water each have distinct growth and decline behavior.

Acceptance Criteria:
- Resource growth depends on terrain and season.
- Food and wood can decline gradually under poor conditions.
- Terrain-based resource caps prevent unbounded growth.
- Mountains and water remain barren.
- Resource abundance is visually noticeable.
- Existing tests pass.

Dependencies:
- TASK-19
- TASK-22

Notes:
- No farming, wildlife, disasters, mining, roles, reproduction, or worldgen rewrite were added.

---

### TASK-22
Title: Smooth Seasonal Color Transitions

Owner: Renderer Agent

Status: Completed

Description:
Implement GitHub Issue #12 by blending seasonal terrain colors during the final day of each season.

Expected Output:
Seasonal map and legend colors gradually transition into the next season rather than snapping at the season boundary.

Acceptance Criteria:
- Seasons last roughly 20 in-game days.
- The final day of each season blends into the next season.
- Map tiles and legend swatches use the same blended color source.
- Seasonal labels show the current transition when blending.
- Existing tests pass.

Dependencies:
- TASK-21

Notes:
- This is renderer/UI polish only; no gameplay, worldgen, pathfinding, resource, water, or balance behavior changed beyond the requested season length.

---

### TASK-21
Title: Update Terrain Legend Seasonal Colors

Owner: Renderer Agent

Status: Completed

Description:
Implement GitHub Issue #11 by making terrain legend swatches use the same season-aware colors as map tiles.

Expected Output:
A terrain legend that always matches the active season's visible map colors.

Acceptance Criteria:
- Map and legend use the shared seasonal color helper.
- Legend swatches change with the current season.
- Legend remains compact and readable.
- Existing tests pass.

Dependencies:
- TASK-20

Notes:
- This is a UI consistency fix only; no gameplay, worldgen, pathfinding, or season mechanics changed.

---

### TASK-20
Title: Add Visible Seasonal Terrain Effects

Owner: Renderer Agent

Status: Completed

Description:
Implement GitHub Issue #10 by making seasons visually noticeable through renderer-only terrain color changes.

Expected Output:
Season-aware map colors that make Spring, Summer, Autumn, and Winter feel distinct without changing tile kinds or gameplay rules.

Acceptance Criteria:
- Seasonal color lookup varies terrain across seasons.
- Wetlands, forests, plains, dry terrain, hills, mountains, and water have visible seasonal variants.
- Tile kinds are not destructively changed by visual effects.
- Water and rivers remain stable water sources.
- Existing tests pass.

Dependencies:
- TASK-19

Notes:
- This uses renderer tinting/color variants only; no droughts, floods, freezing, river removal, or pathfinding changes were added.

---

### TASK-19
Title: Add Season System v1

Owner: Gameplay/Worldgen Agent

Status: Completed

Description:
Implement GitHub Issue #9 by adding simple seasonal changes that affect resource regrowth while keeping water reliable.

Expected Output:
A visible Spring/Summer/Autumn/Winter cycle with logged season changes and season-aware food and wood regrowth.

Acceptance Criteria:
- World starts with a valid season.
- Seasons advance and wrap on schedule.
- Season changes are logged.
- Terrain and season both influence resource regrowth.
- Water remains water across season changes.
- The right panel shows current season state.
- Existing tests pass.

Dependencies:
- TASK-13
- TASK-16
- TASK-17
- TASK-18

Notes:
- This is Season System v1 only; no droughts, floods, freezing, farming, wildlife, or dynamic terrain conversion were added.

---

### TASK-18
Title: Add Terrain Legend UI

Owner: Renderer Agent

Status: Completed

Description:
Implement GitHub Issue #8 by adding a compact terrain and symbol legend to the right-side panel.

Expected Output:
A readable in-game legend with terrain color swatches and basic symbol explanations.

Acceptance Criteria:
- Current terrain kinds have labels.
- Current terrain kinds have colors.
- The right panel renders a compact legend without changing simulation behavior.
- Tests cover terrain label/color coverage.

Dependencies:
- TASK-17

Notes:
- This is a UI-only change; no world generation or agent behavior was changed.

---

### TASK-17
Title: Add Natural Terrain Variety

Owner: Architect Agent

Status: Completed

Description:
Implement GitHub Issue #7 by placing mountains, hills, plains, wetlands, and dry areas naturally using elevation, moisture, and temperature.

Expected Output:
More varied rule-based terrain that renders correctly and keeps existing movement, resources, and survival behavior compatible.

Acceptance Criteria:
- Generated worlds include hills, plains, wetlands, and dry areas under suitable conditions.
- New terrain kinds have renderer colors.
- Water and mountains remain unwalkable; new land terrain remains walkable.
- Resource placement reflects terrain type.
- Existing pathfinding, memory, goals, storage, and renderer tests pass.

Dependencies:
- TASK-13
- TASK-16

Notes:
- No movement costs, farming, minerals, wildlife, or seasonal systems were added.

---

### TASK-16
Title: Add Simple Rivers

Owner: Architect Agent

Status: Completed

Description:
Generate simple rivers from high elevation toward low elevation as part of v0.4 smarter world generation.

Expected Output:
Deterministic river paths that become ordinary unwalkable water tiles and integrate with existing terrain, pathfinding, and agent water behavior.

Acceptance Criteria:
- Rivers appear in generated worlds.
- Rivers generally move downhill from higher elevation to lower elevation.
- River tiles use the existing `water` terrain.
- River water remains unwalkable and pathfinding-compatible.
- Tests cover deterministic rivers, river water tiles, and downhill movement.

Dependencies:
- TASK-13
- TASK-15

Notes:
- This does not add bridges, flooding, erosion, boats, or advanced hydrology.

---

### TASK-15
Title: Add Larger Map Support

Owner: Renderer Agent

Status: Completed

Description:
Increase the default generated world size and add camera panning so the map can be explored without hiding the right-side panel.

Expected Output:
A larger default world with viewport-based rendering, keyboard camera controls, and camera-aware mouse selection.

Acceptance Criteria:
- Default world is noticeably larger.
- Camera panning works with WASD.
- Mouse selection accounts for camera offset.
- The right panel remains visible.
- Tests cover larger world dimensions, spawn walkability, camera conversion, and visible bounds.

Dependencies:
- TASK-13

---

### TASK-13
Title: Add Rule-Based World Generation

Owner: Architect Agent

Status: Completed

Description:
Replace purely random terrain with simple rule-based world generation using natural terrain patterns.

Expected Output:
World generation that produces more believable terrain and resource placement while preserving simulation performance.

Acceptance Criteria:
- Terrain is less uniformly random.
- Elevation, moisture, and temperature maps are generated.
- Water, forests, mountains, and food placement follow readable rules.
- Same seed creates the same terrain/resource layout.
- Different seeds usually create different layouts.
- Tests cover deterministic generation with fixed seeds.

Dependencies:
- TASK-3
- TASK-5
- TASK-9

Notes:
- Implemented in `src/worldgen.py`.
- This is v0.4 Phase 1 only; rivers, seasons, events, wildlife, and world history remain future work.

---

### TASK-14
Title: Prepare v0.3.0 Milestone

Owner: Release Agent

Status: Completed

Description:
Close out the v0.3 colony foundation milestone with documentation, verification, and release notes.

Expected Output:
Updated roadmap, task tracker, changelog, README, and release recommendation.

Acceptance Criteria:
- `python -m pytest` passes.
- `python -m src.main` launches.
- v0.3 completed work is documented.
- Next milestone work is clear.

Dependencies:
- TASK-11

---

### TASK-11
Title: Add Simple Storage

Owner: Gameplay Agent

Status: Completed

Description:
Add basic colony storage so gathered food and wood can support the group rather than only individual carriers.

Expected Output:
A minimal storage model that can hold shared food and wood.

Acceptance Criteria:
- Agents can deposit resources into storage.
- Agents can use stored resources when appropriate.
- Scarcity remains meaningful.
- Tests cover storage interactions.
- Stored totals are visible in the UI.

Dependencies:
- TASK-9

Notes:
- Implemented in `src/colony_storage.py`.
- Storage is abstract; no physical stockpile or hauling system exists yet.

---

### TASK-10
Title: Improve Building Priorities

Owner: Gameplay Agent

Status: Completed

Description:
Refine how villagers decide what to build and when, building on shelter-capacity logic without adding a large construction system.

Expected Output:
Small goal/action scoring refinements for construction priorities.

Acceptance Criteria:
- Shelter construction remains bounded by colony needs.
- Building-related work does not dominate survival goals.
- Tests cover changed construction priority rules.
- The priority system is ready for future building types.

Dependencies:
- TASK-8
- TASK-9

Notes:
- Implemented in `src/building_priorities.py`.
- Shelter remains the only buildable structure for now.

---

### TASK-9
Title: Add Shared Colony Memory

Owner: Gameplay Agent

Status: Completed

Description:
Create a colony-level knowledge system so discoveries made by one agent can benefit the group.

Expected Output:
A shared memory system that tracks known food, water, wood, and shelter locations and allows agents to use that knowledge after checking personal memory.

Acceptance Criteria:
- Knowledge spreads through the colony.
- Agents use personal memory first.
- Agents use colony memory second.
- Agents can seek resources discovered by other agents.
- Survival improves without removing scarcity.
- `python -m pytest` passes.
- `python -m src.main` launches.

Dependencies:
- TASK-3
- TASK-4
- TASK-5

Notes:
- Implemented in `src/colony_memory.py`.
- Verified for water, food, and wood shared-memory consumption.

---

### TASK-1
Title: Create Project Documents

Owner: Docs Agent

Status: Completed

Description:
Establish the base project documentation to guide development and keep agents and humans aligned. This includes README.md, DESIGN.md, ROADMAP.md, and TASKS.md.

Expected Output:
Completed core project documentation files in the repository root.

Acceptance Criteria:
- README.md explains the project concept and run instructions.
- DESIGN.md explains the core simulation loop and design priorities.
- ROADMAP.md outlines planned milestones.
- TASKS.md tracks active, backlog, and completed work.

Dependencies:
- None

---

### TASK-2
Title: Refactor Single-File Prototype

Owner: Architect Agent

Status: Completed

Description:
Split the single-file Pygame prototype into a modular package structure under `src/`.

Expected Output:
A clean modular structure under `src/` with clear imports and separated simulation/rendering responsibilities.

Acceptance Criteria:
- Game launches from `python -m src.main`.
- Imports resolve cleanly.
- Constants live in `src/config.py`.
- Rendering does not control simulation update logic.

Dependencies:
- TASK-1

---

### TASK-3
Title: Add BFS Pathfinding

Owner: Gameplay Agent

Status: Completed

Description:
Implement a generic Breadth-First Search pathfinding system that agents can use to find shortest paths to target tiles.

Expected Output:
A dedicated pathfinding utility module.

Acceptance Criteria:
- `find_path(world, start, destination)` exists.
- Paths avoid water and mountain tiles.
- Unreachable destinations return an empty path.
- Out-of-bounds inputs are handled safely.

Dependencies:
- TASK-2

---

### TASK-4
Title: Add Agent Memory

Owner: Gameplay Agent

Status: Completed

Description:
Give agents personal memory of visible resource locations.

Expected Output:
Agent memory attributes and scan/update logic.

Acceptance Criteria:
- Agents scan surroundings during updates.
- Memory tracks visible food, water, wood, and shelters.
- Depleted or invalid visible resource memories are removed.
- Memory is inspectable for future UI.

Dependencies:
- TASK-2

---

### TASK-5
Title: Add Goal-Based Behavior

Owner: Gameplay Agent

Status: Completed

Description:
Replace purely reactive action selection with a utility-scored, goal-based decision model.

Expected Output:
A goal system where agents evaluate and choose high-level goals based on needs.

Acceptance Criteria:
- Thirsty agents prioritize water.
- Hungry agents prioritize food.
- Tired agents prioritize shelter/sleep.
- Agents default to exploration when needs are stable.
- Survival improves compared with the v0.1 behavior.

Dependencies:
- TASK-4

---

### TASK-6
Title: Add Selected-Agent UI

Owner: Renderer Agent

Status: Completed

Description:
Implement read-only clicking in Pygame to inspect a selected agent or tile.

Expected Output:
Selection highlighting and side-panel details for agents and tiles.

Acceptance Criteria:
- Clicking a tile with an agent selects that agent.
- Clicking an empty tile selects that tile.
- The side panel renders selected agent or tile details.
- Restarting the world clears selection safely.
- Dead selected agents do not crash the UI.

Dependencies:
- TASK-2
- TASK-5

---

### TASK-7
Title: Add Basic Tests

Owner: Tester Agent

Status: Completed

Description:
Write automated unit tests covering core simulation subsystems.

Expected Output:
Pytest tests for pathfinding, world logic, memory, goals, balance rules, and renderer selection helpers.

Acceptance Criteria:
- `python -m pytest` passes.
- Tests verify pathfinding behavior.
- Tests verify world boundary and walkability logic.
- Tests verify agent memory.
- Tests verify goal priority and action selection.
- Tests verify renderer selection safety.

Dependencies:
- TASK-2
- TASK-3
- TASK-4
- TASK-5
- TASK-6

---

### TASK-8
Title: Balance Thirst and Shelter Construction

Owner: Balance Agent

Status: Completed

Description:
Resolve the early thirst pacing and runaway shelter construction balance issues.

Expected Output:
Small readable balance constants and bounded shelter construction rules.

Acceptance Criteria:
- Thirst remains dangerous but less instantly lethal.
- Agents still prioritize water when thirsty.
- Shelter building happens when capacity is lacking.
- Shelter construction slows or stops once capacity is met.
- Tests cover thirst priority, shelter capacity, and wood-gathering deprioritization.

Dependencies:
- TASK-5
- TASK-6
- TASK-7
