# Roadmap

## v0.1 - Basic Simulation

Goal: Create a runnable automated Pygame colony simulation.

Features:
- [x] Random world generation
- [x] Autonomous villagers
- [x] Hunger, thirst, fatigue
- [x] Food and wood
- [x] Shelter building
- [x] Pygame renderer
- [x] Event log

## v0.2 - Smarter Survival

Goal: Make agents survive through modular systems, memory, goals, pathfinding, UI inspection, tests, and basic balance.

Features:
- [x] Refactor into modules
- [x] Add BFS pathfinding
- [x] Add agent memory
- [x] Add goal-based behavior
- [x] Add selected-agent and selected-tile UI
- [x] Add lightweight automated tests
- [x] Balance thirst pacing and shelter construction

Acceptance Criteria:
- [x] Simulation is split into `src/` modules.
- [x] Agents can pathfind toward remembered resources.
- [x] Agents remember visible food, water, wood, and shelters.
- [x] Agents choose high-level goals and execute low-level actions.
- [x] Players can inspect agents and tiles.
- [x] Core systems are covered by pytest.
- [x] Early thirst and runaway shelter construction are reduced.

## v0.3 - Colony Coordination

Goal: Make villagers behave more like a colony by sharing useful knowledge and coordinating around group needs.

Features:
- [x] Add shared colony memory
- [x] Let agents use personal memory first and colony memory second
- [x] Verify shared knowledge is written and read while preserving scarcity
- [x] Improve building priorities
- [x] Add simple storage
- [x] Add movement stuck recovery for path collisions

Notes:
- Shared colony memory is implemented in `src/colony_memory.py`.
- Agents publish visible food, water, wood, and shelters to `world.colony_memory`.
- Seek actions use personal memory first and colony memory second.
- Building priorities are implemented in `src/building_priorities.py`.
- Shelter construction and construction wood gathering are driven by the current building priority.
- Abstract colony storage is implemented in `src/colony_storage.py`.
- Villagers can deposit extra food/wood and eat from stored food.
- Pathfinding can avoid occupied tiles and agents clear blocked paths after repeated stuck ticks.

## v0.4 - Smarter World

Goal: Make the world feel more believable by generating terrain from simple natural rules and allowing the environment to evolve over time.

Features:
- [x] Replace purely random terrain with rule-based world generation
- [x] Generate elevation, moisture, and temperature maps
- [x] Add larger generated maps with camera panning
- [x] Create rivers that flow from high elevation to low elevation
- [x] Place forests based on moisture and temperature
- [x] Place mountains, hills, plains, wetlands, and dry areas naturally
- [ ] Add seasonal changes that affect food growth and water availability
- [ ] Add basic plant/resource regrowth based on biome conditions
- [ ] Add environmental events such as drought, heavy rain, wildfire, or flood
- [ ] Add wildlife spawning based on biome suitability
- [ ] Add world history tracking for major environmental events
- [ ] Expose world-generation settings such as seed, size, water level, forest density, and climate harshness

Acceptance Criteria:
- [x] Worlds no longer look uniformly random.
- [x] Rivers connect logically from high ground toward lower ground.
- [x] Forests appear more often in wet moderate regions.
- [x] Food and wood availability depend on terrain conditions.
- [x] Larger worlds can be inspected without covering the right-side panel.
- [x] Hills, plains, wetlands, and dry areas render and follow expected walkability/resource rules.
- [ ] Seasonal changes visibly affect resource growth.
- [ ] Agents must adapt to world conditions rather than only random resource placement.

Notes:
- Phase 1 world generation is implemented in `src/worldgen.py`.
- Worlds now generate deterministic elevation, moisture, and temperature maps when given a seed.
- Default worlds are larger than the on-screen viewport and can be inspected with WASD camera panning.
- Phase 2 river generation traces simple downhill paths and converts them to existing unwalkable water tiles.
- Issue #7 adds `hill`, `plain`, `wetland`, and `dry` terrain using the existing elevation, moisture, and temperature maps.
- Existing tile kinds remain compatible: `water`, `mountain`, `forest`, and `grass`.
- Seasons, environmental events, wildlife, and history tracking are still future v0.4 work.

## v0.5 - Colony Roles and Production

Goal: Give the colony more structure and long-term survival tools.

Features:
- [ ] Physical storage or stockpile locations
- [ ] Hauling or task claiming for shared resources
- [ ] Roles
- [ ] Farming
- [ ] Phase 1 population replenishment through migration
- [ ] Population cap or carrying capacity
- [ ] Expanded building priorities
- [ ] Job assignment or task claiming

Notes:
- Population growth should start with migration before biological reproduction.
- Migration should depend on stable survival, food surplus, shelter capacity, and population cap.
- Full reproduction should wait until lifecycle and relationship systems exist.

## v0.6 - Social Simulation

Goal: Add relationships and social structure.

Features:
- [ ] Age and lifecycle states
- [ ] Families
- [ ] Friendships and rivalries
- [ ] Leadership
- [ ] Reputation
- [ ] Group decisions
- [ ] Pair bonds and family relationships without scripted romance

## v0.7 - History and Emergence

Goal: Make the world generate stories over time.

Features:
- [ ] Lineage and ancestry tracking
- [ ] Named settlements
- [ ] Major historical events
- [ ] Timeline view
- [ ] Disasters
- [ ] Ruins
- [ ] Myths or legends
