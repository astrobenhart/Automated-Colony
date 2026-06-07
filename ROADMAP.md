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

Status: Complete for v0.4.0.

Features:
- [x] Replace purely random terrain with rule-based world generation
- [x] Generate elevation, moisture, and temperature maps
- [x] Add larger generated maps with camera panning
- [x] Create rivers that flow from high elevation to low elevation
- [x] Place forests based on moisture and temperature
- [x] Place mountains, hills, plains, wetlands, and dry areas naturally
- [x] Add seasonal changes that affect food growth and water availability
- [x] Add basic plant/resource regrowth based on biome conditions
- [x] Add environmental events such as drought, heavy rain, wildfire, or flood
- [x] Add wildlife spawning based on biome suitability
- [x] Add world history tracking for major environmental events
- [x] Expose world-generation settings such as seed, size, water level, forest density, and climate harshness
- [x] Replace player-facing settings UX with generated world identity

Acceptance Criteria:
- [x] Worlds no longer look uniformly random.
- [x] Rivers connect logically from high ground toward lower ground.
- [x] Forests appear more often in wet moderate regions.
- [x] Food and wood availability depend on terrain conditions.
- [x] Larger worlds can be inspected without covering the right-side panel.
- [x] Hills, plains, wetlands, and dry areas render and follow expected walkability/resource rules.
- [x] Seasonal changes visibly affect resource growth.
- [x] Terrain-based resource caps and gradual die-off create long-term ecological pressure.
- [x] Drought and heavy rain events are logged, visible, temporary, and mildly affect resource ecology.
- [x] Ambient wildlife appears based on biome suitability without disrupting villagers.
- [x] Major environmental events are recorded in persistent structured world history.
- [x] World generation can be reproduced and tuned through centralized settings and presets.
- [x] The right panel presents a generated world title, subtitle, survival outlook, and hidden tags.
- [x] Agents must adapt to world conditions rather than only random resource placement.

Notes:
- Phase 1 world generation is implemented in `src/worldgen.py`.
- Worlds now generate deterministic elevation, moisture, and temperature maps when given a seed.
- Default worlds are larger than the on-screen viewport and can be inspected with WASD camera panning.
- Phase 2 river generation traces simple downhill paths and converts them to existing unwalkable water tiles.
- Issue #7 adds `hill`, `plain`, `wetland`, and `dry` terrain using the existing elevation, moisture, and temperature maps.
- Existing tile kinds remain compatible: `water`, `mountain`, `forest`, and `grass`.
- Season System v1 cycles Spring, Summer, Autumn, and Winter over 20-day seasons and changes terrain-based food/wood regrowth without removing water.
- Seasonal terrain colors make Spring, Summer, Autumn, and Winter visually distinct without changing tile kinds, with final-day color blending into the next season.
- Resource ecology now applies terrain and season based growth, caps, and gradual die-off in `src/resource_ecology.py`.
- Environmental Event v1 adds rare drought and heavy rain events in `src/environment_events.py`.
- Wildlife v1 adds ambient rabbits, deer, boar, and waterfowl in `src/wildlife.py`.
- World History v1 records drought and heavy rain beginnings/endings in `src/world_history.py`.
- World generation settings and presets are centralized in `src/worldgen_settings.py`.
- World identity is generated from actual map conditions in `src/world_identity.py`; no setup menu is planned.
- Final v0.4 verification compared normal, wet, dry, forest, and harsh worlds through day 20. Presets changed water, food, wood, and survival pressure, while agents responded through water seeking, food seeking, wood seeking, storage, and shelter construction.
- Survival outlook labels are useful but approximate; future balance passes can tune identity/outlook calibration without blocking v0.4.
- Wildfire, flood, and broader settlement/wildlife history remain future work.

## v0.5 - Colony Roles and Production

Goal: Give the colony more structure and long-term survival tools, turning shelter clusters into early village hubs.

Features:
- [x] Lightweight villager roles as preference modifiers
- [x] Settlement center
- [ ] Village hub behavior around the settlement center
- [ ] Physical storage or stockpile locations
- [ ] Clustered building placement near the village hub
- [ ] Hauling or task claiming for shared resources
- [ ] Farming
- [ ] Local resource use radius
- [ ] Population cap or carrying capacity
- [ ] Expanded building priorities
- [ ] Job assignment or task claiming

Notes:
- Current playtests show believable shelter clustering after early survival pressure.
- Roles v1 is implemented in `src/roles.py` with Generalist, Forager, Builder, and Scout. Roles are soft goal-score preferences, not job assignments; urgent survival needs still dominate.
- Settlement Center v1 is implemented in `src/settlement.py` as a single conceptual village anchor. It is automatically named and placed near the initial villager centroid, tracks living population and radius, and is visible in the right panel and map marker.
- Next v0.5 steps should build on the settlement center with local work radius, physical storage, and clustered building placement.
- Physical stockpiles and building clusters are prerequisites for richer settlement identity and expansion.
- Physical stockpiles, multiple settlements, migration, expansion, and settlement-driven task claiming remain future work.

## v0.6 - Social Simulation

Goal: Add relationships and social structure so stable colonies begin to feel like villages.

Features:
- [ ] Age and lifecycle states
- [ ] Families
- [ ] Friendships and rivalries
- [ ] Leadership
- [ ] Reputation
- [ ] Group decisions
- [ ] Pair bonds and family relationships without scripted romance
- [ ] Social behavior shaped by settlement membership

Notes:
- Social systems should build on stable settlement centers rather than scripted story events.
- Leadership, families, and reputation should affect how villagers organize locally before broader politics exist.

## v0.7 - History and Emergence

Goal: Make the world generate stories over time through named places, movement, lineage, and ruins.

Features:
- [ ] Named settlements
- [ ] Migration between settlements
- [ ] Splinter settlements when resources become scarce
- [ ] Lineage and ancestry tracking
- [ ] Major historical events
- [ ] Timeline view
- [ ] Disasters
- [ ] Ruins
- [ ] Myths or legends

Notes:
- Migration should start as a recovery/expansion mechanism before full reproduction and family history are deeply modeled.
- Splinter settlements should emerge from resource pressure, population pressure, distance, or social conditions.
- Ruins and lineage should connect past settlements to current play rather than appear as isolated flavor.

## v0.8 - Village Formation and Historical Settlements

Goal: Evolve survival colonies into recognizable villages and, eventually, multiple historical settlements with distinct identities.

Roadmap Issue:
- Issue #14: Roadmap: Settlement and Village Formation Systems

Settlement Formation Stages:
- Phase 1: Settlement Center
- Phase 2: Settlement Radius and Local Resource Use
- Phase 3: Physical Stockpiles and Building Clusters
- Phase 4: Expansion and Migration
- Phase 5: Village Identity and History

Features:
- [ ] Settlement centers as explicit anchors for colony activity
- [ ] Village hubs that attract shelter, storage, and production buildings
- [ ] Clustered building placement around hubs
- [ ] Local resource use radius for routine work
- [ ] Expansion when nearby food, wood, or water access becomes strained
- [ ] Migration to recover population or found new settlements
- [ ] Splinter settlements that emerge from pressure rather than scripts
- [ ] Settlement identity, names, founding dates, notable events, and remembered residents
- [ ] Historical links between settlements, ruins, migration, and lineage

Design Notes:
- Current behavior: villagers cluster near shelters, explore locally, and often stabilize in a small area after early die-off.
- Desired future behavior: those clusters become recognizable villages with centers, storage, building clusters, and local work patterns.
- Long-term behavior: worlds can contain multiple settlements with separate identities, histories, migration paths, ruins, and lineages.
- Settlement growth should remain emergent: resource pressure, population needs, shelter capacity, social ties, and geography should drive expansion.

Non-Goals For Now:
- Warfare
- Diplomacy
- Economy
- Politics
- Kingdoms

Notes:
- These are future possibilities, not scheduled systems.
- The near-term path should stay grounded in survival, settlement centers, local work, and village identity before scaling up to larger institutions.
