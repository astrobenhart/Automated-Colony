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
- [x] Central founding start with clustered villager spawn
- [x] Village hub behavior around the settlement center
- [x] Physical storage or stockpile locations
- [x] Simple workshop near the village hub
- [x] Clustered building placement near the village hub
- [x] Local resource use radius
- [x] Expanded building priorities
- [x] Resource reservation v1 for shared targets
- [x] Farming
- [x] Settlement carrying capacity and pressure status

Notes:
- Current playtests show believable shelter clustering after early survival pressure.
- Roles v1 is implemented in `src/roles.py` with Generalist, Forager, Builder, and Scout. Roles are soft goal-score preferences, not job assignments; urgent survival needs still dominate.
- Settlement Center v1 is implemented in `src/settlement.py` as a single conceptual village anchor. It is automatically named and placed near the initial villager centroid, tracks living population and radius, and is visible in the right panel and map marker.
- Central Founding Start v1 establishes the settlement before villagers spawn. The founding tile is chosen by bounded suitability scoring near the map center, and villagers spawn in a deterministic nearby cluster on valid tiles. The exact center is not forced, and no player placement UI is introduced.
- Village Hub Behavior v1 lets the settlement center bias calm exploration and shelter build-site choice without adding a mandatory return-home goal. Scouts can range farther, builders and foragers remain more local, and settlement activity is tracked in a lightweight heatmap for future roads, stockpiles, workshops, and districts.
- Physical Stockpiles v1 adds visible food and wood stockpiles near the settlement. Depositing villagers return resources to adjacent stockpile access tiles, while `ColonyStorage` remains the storage source of truth.
- Workshop v1 adds one basic workshop near the settlement hub. Calm Builders can work there to convert stored wood into building materials, and those materials reduce shelter wood cost when available.
- Local Resource Radius v1 gives the settlement a soft work territory. Agents prefer reachable local food, water, and wood under normal pressure, expand outward when local resources are scarce, and ignore radius penalties for urgent survival needs. Scouts have a weaker local penalty so they can range farther.
- Clustered Building Placement v1 adds autonomous settlement-aware build-site scoring for shelters. It prefers loose clusters near the village hub, avoids stockpiles, workshops, and the settlement center, preserves simple access around important tiles, and uses bounded arithmetic scoring without pathfinding. Full zoning, roads, player placement, and city planning remain future work.
- Expanded Building Priorities v2 reframes construction decisions as centralized settlement needs. The settlement tracks shelter, wood, and materials scores, updates them centrally from population, storage, shelter capacity, and workshop state, and Builders respond to the current need while survival goals still override.
- Resource Reservation v1 adds soft claims for shared food, wood, shelter build sites, and workshop use. Reservations reduce duplicate effort and crowding, expire automatically, release on completion/recovery/death/invalid targets, and allow critical survival overrides. This is not a generic job board, hauling chain, construction queue, or player work-order system.
- Resource Reservation v1 satisfies the v0.5 coordination goal. Full hauling and job assignment are deferred because they are larger logistics systems involving item movement, queues, and multi-step production.
- Farming v1 adds autonomous 2x2 farm plots near the settlement. Farms are created gradually from high settlement food pressure, use bounded local placement scoring without pathfinding, grow once per day with seasonal and environmental-event modifiers, and can be harvested by villagers through the existing food goal. Full agriculture, irrigation, crop choice, player farm placement, and farming UI remain future work.
- Farming activation is calibrated so healthy food storage and local foraging keep pressure low, while sustained shortages can create one farm per day from day 2 onward until the population-based cap is reached.
- Settlement Carrying Capacity v1 adds an explanatory pressure report. It estimates current population support from shelter, food, and water, shows the limiting status, and includes reason lines so a report such as "Food Strained" explains the storage, local food, farm food, and water/shelter context behind it. This is a status/reporting system, not population growth or a hard population gate.
- Workshops should come before full hauling/job assignment. Stockpiles make resources visible; workshops give stored resources a productive use; deeper logistics should come later when there are enough resource destinations to justify the added complexity.
- Next v0.5 steps should build on the settlement center with simple workshops, local work radius, and clustered building placement.
- Physical stockpiles and building clusters are prerequisites for richer settlement identity and expansion.
- Full hauling, withdrawal logistics, job assignment, multiple settlements, migration, expansion, and deeper settlement-driven logistics remain future work.

## Future Logistics / v0.6+

Goal: Add deeper resource logistics only after the village has enough production chains and destinations to justify the complexity.

Features:
- [ ] Full hauling and job assignment system
- [ ] Hauling chains between resource sources, stockpiles, workshops, farms, and future buildings
- [ ] Item stacks or explicit carried-resource destinations
- [ ] Job queues or autonomous job board
- [ ] Inventory and resource reservations beyond simple target claims
- [ ] Multi-step production logistics

Notes:
- Resource Reservation v1 remains the v0.5 coordination layer.
- Full hauling/logistics should remain autonomous unless a later design explicitly introduces player-visible work orders.
- Do not add this system until farming, richer production chains, or multiple resource destinations make it worthwhile.

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

## v0.7 - Mysteries and Wanderers

Goal: Let the living world occasionally surprise the observer with rare visitors, strange events, and unexplained landmarks that create stories without becoming another management layer.

Features:
- [ ] Rare visitor framework
- [ ] Wandering Wizard as one possible visitor
- [ ] Strange hermits, lost knights, travelling merchants, dreaming pilgrims, golden stags, and other unusual passersby
- [ ] Strange events such as meteor strikes, falling stars, auroras, ghost lights, singing forests, sudden mist, or animals gathering silently at night
- [ ] Mystical landmarks such as ancient standing stones, hidden ruins, crystal springs, sleeping giant trees, marked groves, or forgotten shrines
- [ ] Villager reactions to wonders, visitors, and omens
- [ ] History entries for mysteries, arrivals, departures, and strange outcomes

Design Goal:
- The colony simulation should occasionally produce rare and memorable events that surprise the observer.
- The player does not directly control these events.
- They emerge from the world and create stories.
- The goal is wonder, mystery, and unpredictability, not power progression.
- These systems should deepen the screensaver / ant-farm quality of watching the world unfold.

Rare Visitors:
- Visitors are not normal villagers.
- Visitors are autonomous.
- Visitors arrive and leave.
- Visitors should feel unusual.
- Visitors should not become another colony role.
- Example visitors include a Wandering Wizard, Strange Hermit, Lost Knight, Travelling Merchant, Dreaming Pilgrim, and Golden Stag.

Strange Events:
- Examples include Meteor Strike, Falling Star, Aurora, Ghost Lights, Singing Forest, Sudden Mist, and animals gathering silently at night.
- These are examples only; the exact final list should remain open so the world can still surprise the player.
- Events should be bounded, rare, and integrated with history.

Mysteries and Landmarks:
- Examples include Ancient Standing Stone, Hidden Ruin, Crystal Spring, Sleeping Giant Tree, Marked Grove, and Forgotten Shrine.
- Landmarks may appear through world generation, rare events, or visitor interactions.
- Some landmarks should remain partly unexplained.

Example:
- Day 217: A wizard appears at the edge of the map.
- Villagers begin gathering around him.
- Nobody knows why.
- Several days later the wizard leaves.
- Possible outcomes include temporary crop growth, a revealed water source, one villager becoming a Dreamer, a standing stone appearing, or a blessing/curse affecting a small area.
- The exact effect should remain somewhat mysterious.

Screensaver Principle:
- The project is partly a simulation and partly a living screensaver.
- Rare events should occasionally create moments that make the observer stop and watch.
- The simulation should be capable of surprising the player even after many hours.

Non-Goals:
- Rare means rare; mysteries should not happen constantly.
- The user should not summon visitors or command them.
- Effects should not dominate survival systems.
- This should not become a spell system, RPG quest system, or another colony management layer.
- Some mystery should remain unexplained.

Future Architecture Notes:
- Prefer generic systems over a hardcoded wizard.
- Possible future modules: `visitors.py`, `mysteries.py`, `magical_events.py`.
- Possible concepts: `Visitor`, `MysteryEvent`, `MagicalEffect`, rare spawn scheduler, bounded duration, history integration, villager reaction hooks, and renderer markers.
- The wizard should be one possible visitor, not the entire system.

## v0.8 - History and Emergence

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

## v0.9 - Village Formation and Historical Settlements

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
