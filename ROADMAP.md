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
- [ ] Add simple storage

Notes:
- Shared colony memory is implemented in `src/colony_memory.py`.
- Agents publish visible food, water, wood, and shelters to `world.colony_memory`.
- Seek actions use personal memory first and colony memory second.
- Building priorities are implemented in `src/building_priorities.py`.
- Shelter construction and construction wood gathering are driven by the current building priority.

## v0.4 - Smarter World

Goal: Make the world feel more believable by generating terrain from simple natural rules and allowing the environment to evolve over time.

Features:
- [ ] Replace purely random terrain with rule-based world generation
- [ ] Generate elevation, moisture, and temperature maps
- [ ] Create rivers that flow from high elevation to low elevation
- [ ] Place forests based on moisture, temperature, and nearby water
- [ ] Place mountains, hills, plains, wetlands, and dry areas naturally
- [ ] Add seasonal changes that affect food growth and water availability
- [ ] Add basic plant/resource regrowth based on biome conditions
- [ ] Add environmental events such as drought, heavy rain, wildfire, or flood
- [ ] Add wildlife spawning based on biome suitability
- [ ] Add world history tracking for major environmental events
- [ ] Expose world-generation settings such as seed, size, water level, forest density, and climate harshness

Acceptance Criteria:
- Worlds no longer look uniformly random.
- Rivers connect logically from high ground toward lower ground.
- Forests appear more often near water or in wet regions.
- Food and wood availability depend on biome.
- Seasonal changes visibly affect resource growth.
- Agents must adapt to world conditions rather than only random resource placement.

## v0.5 - Colony Roles and Production

Goal: Give the colony more structure and long-term survival tools.

Features:
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
