# Roadmap

Current Development Branch: v0.9-development

## North Star - Slow Autonomous Village Simulation

Automated Colony is moving from an automated survival colony toward a slow autonomous generational village simulation.

The world should feel lived in.

The player should feel like they are observing a place with homes, paths, jobs, routines, households, children, elders, births, deaths, inherited traits, memories, history, land changed by people, and land changed by natural forces.

The settlement should not feel like a blank map where every villager starts from scratch. The player is not founding every story. The player is arriving partway through ongoing village life.

As of v0.8, the foundational generational simulation is complete. Future development should now ask a different question:

"What memorable stories naturally emerge from this village?"

Perfect realism is no longer the main objective. Interesting, believable villages are. When a more accurate simulation conflicts with a more memorable emergent story, prefer the story unless realism directly improves it.

Long-term direction:
- A slow autonomous village simulation where generations of villagers live, work, form households, reproduce, inherit traits, reshape the land, and create emergent stories over long periods of time.
- The project is not a colony manager. The observer watches the world unfold; they do not assign jobs, command households, place every building, or micromanage production.
- Survival remains important, but the future emphasis is memorable moments, personality, traditions, relationships, mystery, atmosphere, village identity, generational memory, and visible accumulated history.

## Release Notes

### v0.7 - Lived-In Settlements

Status: Released.

Major gameplay additions:
- Pre-seeded lived-in settlements with visible homes, workplaces, paths, households, and villagers distributed around the village.
- Daily village rhythms, day progress HUD, settlement maturity scenarios, and compact colony health visibility.
- Seasonal food ecology, food spoilage, agriculture foundations, crop fields, seed reserves, and farm workplace specialization.
- Household foundations, relationship states, social bonds, seeded routines, memories, and starting Chronicle entries.

Major architectural additions:
- Generic workplace foundation for storage, farms, workshops, and village center.
- Path traffic and wear system with path-preferred pathfinding.
- Lifecycle, family, inheritance, household lineage, and death-history structures prepared for v0.8.
- Simulation LOD framework separating visual, task, needs, social, planner, and history update tiers.

Performance improvements:
- Rotating villager task updates.
- Hourly needs updates with pre-LOD balance preserved.
- Daily settlement planning and social updates.
- Developer-facing LOD timing counters through `World.lod_stats` and `World.lod_report()`.

Known limitations:
- No reproduction, children, inheritance logic, marriage, romance, family trees, or natural old-age death yet.
- Save/load is not a full gameplay system yet; generation records are JSON-safe foundations only.
- Full 10/30/50-year tick-level validation remains expensive; daily/calendar long-run validation is stable.

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

Status: Complete for v0.5.0.

Features:
- [x] Lightweight villager roles as preference modifiers
- [x] Role-based villager colors for at-a-glance readability
- [x] Settlement center
- [x] Central founding start with clustered villager spawn
- [x] Village hub behavior around the settlement center
- [x] Physical storage or stockpile locations
- [x] Simple workshop near the village hub
- [x] Clustered building placement near the village hub
- [x] Local resource use radius
- [x] Expanded building priorities / settlement needs
- [x] Resource reservation v1 for shared targets
- [x] Farming v1
- [x] Settlement carrying capacity and pressure status, measurement-only
- [x] Simplified right panel colony and simulation summaries

Notes:
- v0.5.0 - Colony Roles and Production is closed out. The simulation has evolved from a survival sandbox into a true settlement simulator.
- Current playtests show believable shelter clustering after early survival pressure.
- Roles v1 is implemented in `src/roles.py` with Generalist, Forager, Builder, and Scout. Roles are soft goal-score preferences, not job assignments; urgent survival needs still dominate.
- Role colors are restored as a gameplay readability feature. Generalists, Foragers, Builders, and Scouts render with distinct high-contrast colors so the colony can be understood at a glance without selecting villagers.
- Settlement Center v1 is implemented in `src/settlement.py` as a single conceptual village anchor. It is automatically named and founded near the map center on valid terrain before villagers spawn, tracks living population and radius, and is visible in the right panel and map marker.
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
- Right Panel Summary v1 makes the default panel shorter and more player-facing. It keeps world identity, compact Day/Year/Season/Speed information, colony status, resources, capped reasons, and recent events without showing population as a capacity denominator.
- Workshops should come before full hauling/job assignment. Stockpiles make resources visible; workshops give stored resources a productive use; deeper logistics should come later when there are enough resource destinations to justify the added complexity.
- Physical stockpiles and building clusters are prerequisites for richer settlement identity and expansion.
- Full hauling, withdrawal logistics, job assignment, multiple settlements, migration, expansion, and deeper settlement-driven logistics remain future work.

## v0.6 - Villager Life and Social Foundations

Goal: Make villagers feel more like individuals and settlement members without adding fragile population churn.

Features:
- [x] Lifecycle labels without old-age death
- [x] Simple traits
- [x] Role-based resource discovery radius
- [x] State labels for current villager condition
- [x] Basic social memory or familiarity
- [x] Overlay Framework v1 with Villagers overlay
- [x] Influence foundation for future leadership
- [x] Appearance System v1 with 8-bit villager portraits
- [x] Death memory and remembrance as flavor/history
- [x] History Overlay GUI as a read-only village chronicle
- [x] Settlement identity and belonging
- [x] Optional Social Bond Labels

Notes:
- v0.5 created the stable settlement economy. v0.6 should make the people inside that settlement feel more individual without making the village fragile.
- Lifecycle Labels v1 assigns each villager a static Adult or Elder label at creation. The label appears in selected-villager details and has no aging progression, old-age death, reproduction, or survival impact.
- Simple Traits v1 assigns each villager one static display-only trait at creation. Traits include positive, neutral, and imperfect labels, appear in selected-villager details, and have no gameplay modifiers yet.
- Role-Based Resource Discovery Radius v1 gives Scouts the broadest food/wood/water discovery, makes Foragers naturally better at finding food, and keeps Builders locally aware without making discovery dependent on any one role.
- State Labels v1 computes a selected-villager `State` from existing needs and action fields. State describes what the villager is doing or experiencing now; Mood and morale remain future work.
- Social Memory v1 records repeated nearby presence once per day. Villagers progress through neutral Stranger, Seen, Acquainted, and Familiar labels, store last-seen day metadata, and show a compact selected-villager `Knows` summary without adding friendships, relationships, events, or behavior effects.
- Overlay Framework v1 adds reusable pygame-gui overlays for focused observation. Villagers is the first overlay, opened with `V`, and uses a master/detail layout for villager inspection while the right panel stays compact. Overlays are observer tools, not command tools.
- Influence Foundation v1 computes soft social importance from recent incoming familiarity. Influence labels are Low, Emerging, Notable, and Respected, appear in the Villagers overlay, update peak influence metadata, and do not select formal leaders or affect behavior.
- Appearance System v1 assigns stable `appearance_seed` and `appearance_type` identity metadata. The Villagers overlay uses procedural layered full-body 8-bit character sprites with outline, skin, hair, eyes, body, role-colored clothing, and accent pixels; elders render with grey hair. The selected villager pane is an RPG-style character card focused on identity, State, Influence, and familiar villagers rather than raw simulation telemetry.
- Death Memory v1 creates permanent Death Records when villagers die, records one readable world-history entry, and gives familiar villagers a temporary personal `Remembering: Name` line. This is memory and history flavor only; it does not add morale penalties, productivity penalties, graves, funerals, ghosts, resurrection, or legacy mechanics.
- History Overlay v1 adds a read-only Chronicle opened with `H`. It shows recent history entries, active remembrance lines, and compact remembered-dead cards using story-facing language and readable season/year dates. It is not a death viewer, graveyard UI, debug log, or management tool.
- Settlement Identity v1 gives villagers stable home and birth settlement fields, displays Home on character cards, and lets death history / Chronicle wording use names such as `Rowan of Oakvale`. This is belonging and future migration groundwork only; it adds no behavior bonuses, same-settlement familiarity changes, politics, factions, migration, or conflict.
- Social Bond Labels v1 replace the old pair/family-label idea with non-romantic, non-family display labels derived from existing familiarity. Character cards may show community labels such as Familiar, Friend, Close Friend, and Trusted Companion. These labels do not affect behavior, remembrance, influence, settlement membership, survival, or social-memory growth.
- Do not add old-age death yet.
- Do not add reproduction, children, romance, households, inheritance, or full family trees in v0.6. These are now explicit future architecture targets, starting with lived-in village and household foundations.
- Do not let social systems override survival needs.
- Do not create guaranteed village extinction.
- Lifecycle states in v0.6 should be story labels and behavior flavor.
- Example lifecycle labels: Adult and Elder.
- Elders may move slower, work less often, influence leadership/memory/history, or be more likely to appear in notable events.
- Elders should not automatically die of old age until a renewal system exists.
- Age in v0.6 is identity/story, not attrition.

## v0.7 - Lived-In Settlement Foundation

Goal: Make the default experience feel like arriving at an existing village already in progress, not watching blank-slate survivors found every story from scratch.

Features:
- [x] Pre-seeded village start Phase 1: central village location, visible homes, and home-distributed villagers
- [x] Homes as village anchors
- [x] Workplace placeholders for farms, storage, workshops, and future professions
- [x] Daily schedule foundation
- [x] Day progress HUD bar
- [x] Seasonal wild food regeneration
- [x] Food spoilage
- [x] Farm-ready food economy foundations
- [x] Crop fields
- [x] Planting cycle
- [x] Seasonal harvests
- [x] Stored seed reserves
- [x] Farm workplace specialization
- [x] Household foundations without full reproduction yet
- [x] Pre-generated village paths or simple worn-path tiles
- [x] Mixed lifecycle starting population
- [x] Pre-existing roles, routines, relationships, social bonds, and memories
- [x] Starting village history / Chronicle seed entries
- [x] Architecture support for future reproduction, children, parents, inherited traits, aging progression, household membership, family history, births, and deaths
- [x] Scenario framing for different starting settlement maturity levels
- [x] Simulation level-of-detail planning for 30-60 villagers

Starting Scenarios:
- Pioneer Camp: a 0-2 year frontier start with 12-20 villagers, few homes, limited stores, sparse paths, and short Chronicle history.
- Growing Village: the default v0.7 start, with 30-60 villagers, homes, farms, paths, storage, workplace placeholders, simple households, roles, routines, social bonds, and seed Chronicle entries.
- Mature Settlement: a 20-50 year start with larger population, more homes, stronger social memory, older paths, and deeper Chronicle context.
- Ancient Hamlet: a 50+ year start with old households, stronger traditions, dense social bonds, longer Chronicle history, and more mysterious folklore.
- Market Town: future scenario with 100-200 villagers, districts, more professions, and delivery/resource networks.

Notes:
- The starting world generator should create an initial social fabric, not just terrain and resources.
- The player should feel like the village existed before observation began.
- Phase 1 of the pre-seeded village start creates 8-15 visible homes around the founded settlement center, then spawns the default 30-60 villager population on or beside those homes.
- Multiple villagers may occupy the same tile, including at startup homes. Occupancy must not block spawning or core movement, which keeps future households from creating pathfinding deadlocks.
- Paths, farms, storage expansion, social familiarity seeding, history seeding, schedules, households, reproduction, and delivery systems remain outside Phase 1.
- Paths are high priority because they visually communicate that people live here.
- v0.7 can begin with generated paths between homes, farms, storage, and workplaces before adding dynamic path wear.
- Daily routines should be slow and readable: wake, eat, go to workplace, work, rest or socialize, return home, eat, household time, sleep.
- A complete in-game day may eventually take several real-world hours in screensaver mode.
- v0.7 should prepare for reproduction and inheritance without implementing them casually as population counters.
- No micromanagement UI, job assignment, work orders, household controls, romance drama, politics, or formal leaders are added.

## v0.7.1 - Living Village

Goal: Village Structure. Make the settlement legible as a living village with visible priorities, working housing construction, paths, households, relationships, and readable daily rhythms.

### Settlement Visibility
- [x] Settlement priorities panel
- [x] Food current/target display
- [x] Water current/target display
- [x] Wood current/target display
- [x] Housing current/target display

### Housing & Construction
- [x] Housing demand generation
- [x] Builder assignment
- [x] Construction site creation
- [x] House completion increases capacity

### Paths
- [x] Pre-seeded village paths
- [x] Path wear system
- [x] Path traffic tracking
- [x] Path-preferred pathfinding

### Households
- [x] Household data model
- [x] Household assignment
- [x] Household display in villager UI
- [x] Household member display

### Relationships
- [x] Stranger relationship state
- [x] Known relationship state
- [x] Familiar relationship state
- [x] Friend relationship state
- [x] Relationship display in villager UI

### Daily Rhythms
- [x] Morning phase
- [x] Day phase
- [x] Evening phase
- [x] Night phase
- [x] Return-home behavior

### Generational Foundations
- [x] parent_ids support
- [x] child_ids support
- [x] generation support
- [x] household_id support
- [x] life stage architecture

Notes:
- v0.7.1 is the focused bridge from settlement simulation to village simulation.
- Paths are the main remaining structural gap for Living Village.
- Households remain village units at this milestone, not marriage, romance, reproduction, inheritance, family trees, or legal family membership.
- Relationship states describe familiarity only and do not drive romance, reproduction, labor assignment, politics, or inheritance.
- Reproduction, inheritance, children, family continuity, and generational history remain upcoming priorities for v0.8.

## v0.8 - Generational Village

Goal: Prove the smallest complete generational loop.

Core question:
Can a village replace itself across generations?

v0.8 is intentionally narrow. It should prove believable continuity and long-term village life without expanding into a complete family simulation.

### Phase 1 - Partnerships

Purpose:
Create stable long-term pair bonds that can support later generational systems.

Features:
- [x] Partnership formation
- [x] Household partnerships

Notes:
- Partnerships are social bonds, not romance simulation.
- No marriage system.
- No romance drama.
- No legal family structures.

### Phase 2 - Births

Purpose:
Introduce population renewal.

Features:
- [x] Reproduction system
- [x] Birth events

Notes:
- Births should emerge from established partnerships.
- Do not treat reproduction as a simple population counter.
- Pregnancy mechanics are deferred unless explicitly needed later.

### Phase 3 - Children

Purpose:
Allow villagers to progress through life stages.

Features:
- [x] Child lifecycle
- [x] Aging progression
- [x] Workforce entry

Notes:
- Children remain members of their household.
- Children eventually become working adults.
- Avoid education systems or child-specific professions.

### Phase 4 - Family Identity

Purpose:
Create continuity between generations.

Features:
- [x] Family relationships
- [x] Family memories
- [x] Trait inheritance

Notes:
- Children inherit traits from parents with variation.
- Family memories should feed the Chronicle and village history systems.
- Families are persistent lineage/history entities, separate from households.
- Family identity is permanent and survives household movement.
- Full family tree UI, surnames, reputation, inheritance law, and genealogy visualization remain future enhancements.

### Phase 5 - Renewal

Purpose:
Close the generational loop.

Features:
- [x] Household succession
- [x] Natural death from aging
- [x] Family Chronicle integration

Notes:
- Villages must be capable of replacing older generations naturally.
- Deaths should connect to renewal rather than creating automatic settlement collapse.
- Old-age death is probabilistic and lifespan-based rather than fixed-age.
- Household heads are succeeded by a surviving partner, adult child, or oldest adult resident.
- Household division and family passing events feed the Chronicle without adding inheritance law or family-tree UI.

### Future Backlog - Not Core v0.8
- [ ] Family trees
- [ ] Family reputation

Status:
Future enhancement after the core generational loop is proven.

Reasons:
- Family trees are primarily visualization and record-keeping rather than simulation behavior.
- Family reputation does not contribute to proving the first generational loop and adds additional social complexity.

Notes:
- v0.8 exists to prove the first generational loop.
- Keep implementation intentionally small.
- Prioritize simulation behavior over UI complexity.
- Avoid pregnancy mechanics, inheritance law systems, romance drama, politics, detailed domestic economies, and complex social simulation.
- Focus on partnerships, births, children, aging, trait inheritance, succession, natural death, and village renewal.
- Residential planning should use houses and housing capacity. Legacy shelter terminology remains only for completed-history notes and compatibility debt.
- Residential growth should emerge from households, overcrowding, house expansion, and new household formation rather than artificial future housing reserves.
- Family trees and family reputation are secondary to proving long-term village continuity.

Success Criteria:
- Partnerships form.
- Children are born.
- Children age into working adults.
- Traits inherit with variation.
- Family relationships and memories persist.
- Elder villagers can die of old age.
- Households can continue through successors.
- The village can continue into the next generation without advanced social simulation systems.

### Release Validation

Purpose:

Validate that the first complete generational simulation remains stable over long-running autonomous play.

Validation checklist:

- [x] 50-year autonomous simulation
- [x] 100-year autonomous simulation
- [x] Population remains stable
- [x] Households persist across generations
- [x] Families continue beyond founders
- [x] Renderer performance remains stable
- [x] Chronicle continues to generate interesting historical events
- [x] No long-term simulation deadlocks
- [x] No irreversible resource collapse
- [x] No runaway population explosion
- [x] No extinction under normal starting conditions

Notes:

- This is a validation milestone, not a feature milestone.
- Prefer identifying balancing issues over adding new systems.
- Any failures should become GitHub issues rather than expanding the scope of v0.8.
- v0.8 is accepted for release. Long-matrix headless validation throughput remains future optimization work, not a release blocker.

### Release Blocker - Century-Scale Population Renewal

- [x] Investigate why births no longer replace natural deaths during century-scale simulations despite functioning partnerships, households, residential growth, succession, and family systems.

Completion criteria:

- Root cause identified.
- Demographic investigation completed.
- Investigation report written.
- Evidence gathered before any gameplay balancing begins.

## Current Development - v0.9 Stories

Purpose:

Transform the simulation from a functioning generational village into one that creates memorable stories.

The emphasis is character, relationships, village identity, atmosphere, mystery, and the Chronicle. Systems should stay lightweight and observable. v0.9 should make the player think, "I can't believe that happened," rather than, "The simulation was technically impressive."

Design priorities:

- Prefer memorable emergent stories over stricter realism.
- Keep behaviour autonomous and readable.
- Avoid micromanagement, player work orders, social spreadsheets, and complex management UI.
- Use existing households, families, memories, and Chronicle systems as the foundation.
- Let rare events remain rare so they feel meaningful.
- Treat presentation as a first-class partner to simulation. The simulation decides what happened; presentation decides how it feels to watch.
- After the current social and polish work, visual architecture becomes the primary development focus.

### Phase 1 - Village Society

Purpose:

Villagers should begin to feel like members of a community rather than isolated workers.

Possible features:

- [x] Friendships
- [x] Village Gatherings
- [x] Shared Moments
- [x] Celebrations
- [x] Living Community

#### Friendships

Purpose:

Allow villagers to remember people they repeatedly share life with.

Friendships should remain the foundation for later social behaviours such as favourite companions, mourning, visiting, shared moments, celebrations, romance, and Chronicle stories.

#### Village Gatherings

Purpose:

Allow villagers to naturally congregate during free time.

Gatherings should emerge from existing friendships, families, households, idle behaviour, and future visitor systems. The system should create opportunities for villagers to spend time together without introducing explicit schedules.

Expected emergent behaviours include:

- friends gathering
- families gathering
- visiting households
- shared meals
- children playing
- wanderers joining gatherings

These are outcomes of the gathering system, not independent systems.

#### Shared Moments

Purpose:

Represent small everyday social interactions.

Examples include:

- sharing meals
- resting together
- sitting together
- chatting
- warming by a fire
- watching village events

Shared meals are one type of shared moment, not a standalone system.

#### Celebrations

Purpose:

Represent significant events in village life.

Celebrations should include joyful events, seasonal traditions, community milestones, and solemn ceremonies. They should integrate naturally with families, friendships, gatherings, and the Chronicle.

Possible examples:

- Harvest Festival
- Founding Day
- First Snow
- birth celebrations
- coming of age
- seasonal festivals
- open cremation ceremonies

Open cremations should become an important village ceremony. When a respected villager dies, the community may gather outside the settlement for a funeral fire. Family, close friends, and other villagers may attend depending on their relationships.

The event should strengthen the feeling that the village remembers its people rather than simply removing them from the simulation.

Mourning is not a standalone system. It should emerge through friendships, celebrations, and the Chronicle when meaningful relationships are lost.

#### Living Community

Purpose:

Let the village gradually develop recognisable social groups and traditions.

The player should begin noticing:

- villagers who often spend time together
- families remaining close
- regular gathering places
- recurring community traditions

These behaviours should emerge naturally from the interaction of the underlying systems rather than explicit scripting.

Notes:

- Keep systems lightweight.
- Avoid complex social simulation.
- Prioritise visible moments that can become memories or Chronicle entries.
- Systems should create behaviours.
- Behaviours should not become separate systems.
- Whenever multiple roadmap items can naturally emerge from a single gameplay system, prefer implementing the single underlying system rather than several narrowly focused mechanics.
- The player should observe these behaviours emerging naturally without the simulation explicitly managing each one.
- This principle should guide all future social systems.

### Phase 2 - Romance

Purpose:

Give partnerships more personality without turning the project into a dating simulator.

Possible features:

- [x] Affection growing over time
- [x] Spending free time together
- [x] Relationship Mood

Do not implement:

- jealousy
- love triangles
- dating mechanics
- relationship graphs

Notes:

- Romance should be subtle, warm, and generational.
- Partnerships remain stable adult bonds, not player-managed relationships.

### Phase 3 - Wanderers

Purpose:

The outside world should occasionally visit the village.

Possible features:

- [x] Shared Wanderer framework
- [x] Main roads to the wider world
- [x] Travelling merchants
- [x] Storytellers
- [x] Hunters
- [x] Pilgrims
- [x] Scholars
- [x] Refugees
- [x] Craftsmen
- [x] Arrival, departure, and stay decisions
- [x] Visitor memories and Chronicle entries

Notes:

- Some visitors leave.
- Some visitors stay.
- Some become memorable members of the village.
- Visitor types should plug into shared behaviour profiles rather than becoming separate systems.
- Visitors should be autonomous and should not become player-assigned colony roles.

## Current Development – Polish & Quality

Purpose:

Improve the quality, readability, presentation and consistency of existing systems before continuing feature development.

These tasks are intentionally focused and should generally be completed before continuing with later roadmap milestones.

### Permanent World Roads

Priority:
Highest

Purpose:

Roads generated during world creation represent permanent connections to the outside world.

These roads should never decay into paths or terrain. They are part of the world itself rather than player-created paths.

Notes:

- Permanent roads should not decay.
- Villager-created paths should continue behaving normally.
- Future caravans, wanderers and world events will reuse these roads.

### Village Chronicle Export

Priority:
Highest

Purpose:

Replace the current scrolling history log with a persistent village Chronicle.

Notes:

- Export the Chronicle as Markdown.
- Store outside the running game.
- Organise using headings.
- Group by year and season.
- Read like a historical record rather than a debug log.
- Future Chronicle systems should continue writing into this document.
- The existing in-game History panel may remain as a lightweight recent-events view.

### Persistent Villager Names

Priority:
Highest

Purpose:

Every villager should receive a proper first and last name.

Notes:

- Children receive names at birth.
- No villager should retain placeholder names such as "Child 23".
- Names persist throughout life.
- Chronicle entries should always use proper names.

### Family Surnames

Priority:
Highest

Purpose:

Family names should naturally follow partnerships and children.

Notes:

- Villagers have first name + surname.
- During partnership the woman adopts the household surname.
- Children inherit the household surname.
- Family identity should become obvious through names.
- This should integrate naturally with the existing Family system.

### Season Transition Optimisation

Priority:
High

Purpose:

Season transitions should remain visually attractive without causing repeated renderer rebuilds.

Notes:

- Seasonal visual changes should occur once per day.
- Avoid sub-day terrain regeneration.
- Preserve existing renderer architecture.
- Maintain smooth performance.

### Natural Rivers and Lakes

Priority:
High

Purpose:

Improve world generation to create more believable waterways.

Notes:

Replace scattered puddle-like lakes with:

- one or two natural lakes
- rivers connecting lakes where appropriate
- or standalone rivers

Generate a permanent bridge where a road crosses a river.

The bridge should simply behave as normal walkable terrain.

Do NOT introduce bridge construction gameplay.

### GUI Scroll Stability

Priority:
Medium

Purpose:

Fix the scrolling behaviour within inspection and diagnostic panels.

Notes:

- The scrollbar should remain stable while scrolling.
- Remove unintended automatic movement.

### Phase 4 - Mysteries

Purpose:

The world should feel larger, older, and stranger than the village.

Possible features:

- [x] Strange lights
- [ ] Ancient ruins
- [ ] Magical weather
- [ ] Forgotten shrines
- [ ] Mysterious travellers
- [ ] Impossible events
- [ ] Unusual creatures
- [ ] Villager reactions to omens and wonders
- [ ] Chronicle entries for strange events

Notes:

- Keep explanations intentionally ambiguous.
- Mysteries should create curiosity rather than provide answers.
- Rare mysteries are stronger than constant mysteries.
- Many mysteries should be presentation-led rather than mechanics-led. The simulation may only need to decide that something was witnessed; the Presentation Layer should make it memorable.
- Avoid explaining mysteries through resource effects, quests, or combat unless a future milestone explicitly chooses that direction.

### Phase 5 - Living Chronicle

Purpose:

The Chronicle should become one of the defining features of Automated Colony.

Possible features:

- [ ] Village legends
- [ ] Famous families
- [ ] Remembered heroes
- [ ] Traditions
- [ ] Anniversaries
- [ ] Historical references
- [ ] Stories passed through generations
- [ ] Chronicle callbacks to older events

Notes:

- The Chronicle should feel like reading the history of a real place.
- Avoid spam. Prioritise events that change how the village will be remembered.
- Use families, households, partnerships, deaths, visitors, mysteries, and disasters as story anchors.

### Phase 6 - Personality

Purpose:

Villagers should become recognisable individuals.

Possible features:

- [ ] Habits
- [ ] Quirks
- [ ] Favourite places
- [ ] Favourite people
- [ ] Personal ambitions
- [ ] Reputation
- [ ] Memorable achievements
- [ ] Personality-informed memories and Chronicle mentions

Notes:

- Avoid micromanagement.
- Keep behaviour emergent.
- Personality should help explain memorable moments, not become a stat sheet.

## Planned Follow-Up - v0.9.1 Living World

Purpose:

Transform Automated Colony into a beautiful retro simulation that players enjoy simply watching.

This release focuses almost entirely on presentation architecture and visual experience. The simulation should remain largely unchanged. The renderer becomes presentation-first rather than debug-first.

Architectural intent:

Simulation
    -> Presentation Layer
    -> Renderer
    -> Display

The simulation remains responsible for decisions, world state, AI, jobs, relationships, weather state, season state, and history. The Presentation Layer becomes responsible for interpolation, animation, easing, sprites, shadows, particles, lighting, wind, foliage, water motion, camera polish, and visual effects. The renderer draws the presentation state.

Visual inspiration should come from games such as Hyper Light Drifter and Stardew Valley in terms of fluid motion, readable silhouettes, satisfying colour palettes, ambient life, and environmental storytelling. Do not copy their artwork. Learn from how their worlds feel alive even when nothing important is happening.

### Presentation Layer Implementation Plan

This section is the engineering roadmap for the renderer overhaul. It is organised in three levels:

1. Vision - why the Presentation Layer exists.
2. Milestones - the order in which architecture should be built.
3. Implementation checklists - focused work items that can become daily development tasks.

Progress:

- [x] Engine
- [x] Scene
- [x] Time
- [x] Observer Camera
- [x] Intent Layer
- [ ] Entities
- [ ] Motion
- [ ] Animation
- [ ] Environment
- [ ] Renderer Migration
- [ ] Visual Content

#### Level 1 - Vision

Purpose:

Make Automated Colony feel fluid, expressive and continuous while remaining driven by deterministic simulation.

Principles:

- Simulation decides.
- Intent plans.
- Presentation performs.
- Presentation remembers.
- Presentation interpolates.
- Renderer draws.
- Simulation should remain deterministic.
- Presentation should become the only place where time flows continuously.
- Renderer should eventually consume Presentation Scene data exclusively.
- The renderer should eventually be replaceable without modifying simulation systems.

The end goal is not prettier graphics by themselves. The end goal is a living world whose presentation makes simulation stories readable, emotional and watchable without moving gameplay decisions into visual code.

#### Level 2 - Milestone Order

Implementation should proceed in this order:

1. Presentation Foundations
2. Presentation World
3. Intent Layer
4. Presentation Motion
5. Presentation Environment
6. Renderer Migration
7. Visual Content

Dependencies:

- Presentation World depends on Presentation Foundations.
- Intent Layer depends on Presentation World.
- Presentation Motion depends on Presentation World and Intent Layer.
- Presentation Environment depends on Presentation World.
- Renderer Migration depends on Presentation World and should absorb Motion and Environment snapshots as they mature.
- Visual Content depends on Renderer Migration and the relevant Presentation systems.

Do not start artwork-heavy tasks until the architecture can support them cleanly.

#### Milestone 1 - Presentation Foundations

Status:
Complete.

Purpose:

Establish the first Presentation Engine between simulation and renderer.

Responsibilities:

- Prove the Simulation -> Presentation -> Renderer boundary.
- Keep headless simulation independent.
- Move continuous villager movement state out of gameplay objects.
- Provide immutable presentation snapshots for agent rendering.

Completed checklist:

- [x] Presentation Engine
- [x] PresentationAgent
- [x] PresentationSnapshot
- [x] Agent interpolation
- [x] Easing for basic movement
- [x] Renderer consumes agent presentation snapshots
- [x] Presentation Scene root object
- [x] Presentation object lifetime for agents
- [x] Presentation Time
- [x] Headless compatibility
- [x] Boundary tests
- [x] Documentation

Completion criteria:

- Renderer no longer asks gameplay agents for render positions.
- Agent render-motion state no longer lives on simulation agents.
- Headless validation can run without Presentation.
- Focused tests prove simulation remains authoritative.

Long-term architectural role:

This milestone is the foundation, not the finished layer. It proves the idea with agents only. Future work should widen the same pattern instead of adding direct renderer queries.

#### Milestone 2 - Presentation World

Purpose:

Create the Presentation Scene as the visual representation of the simulation.

Responsibilities:

- Hold scene-level presentation state.
- Own presentation time.
- Own Observer Camera presentation.
- Register long-lived presentation entities.
- Generate renderer-facing snapshots.
- Define presentation ownership boundaries.

Dependencies:

- Depends on Presentation Foundations.

Implementation checklist:

- [x] Presentation Scene root object
- [x] Presentation Time
- [x] Observer Camera
- [x] Presentation object lifetime for agents
- [ ] General Presentation Entities registry
- [x] World-space coordinates
- [ ] Presentation ownership boundaries
- [x] Agent snapshot generation through Presentation Scene
- [ ] Layer-wide snapshot generation
- [x] Renderer receives Presentation Scene snapshot for agents
- [x] Documentation
- [x] Tests

Completion criteria:

- Presentation Scene exists as the renderer-facing root.
- Renderer begins consuming Presentation Scene data rather than gameplay state for at least one additional domain beyond agents.
- Presentation time exists separately from simulation tick.
- Observer Camera boundaries are documented and tested.
- Headless simulation remains independent.

Common mistakes to avoid:

- Do not make Presentation the new simulation.
- Do not move terrain mutation, pathfinding, resource state or event authorship into Presentation.
- Do not attempt a full renderer rewrite in one task.

Long-term architectural role:

Presentation World is the bridge from one interpolated feature to a true scene model. It gives all later motion, animation, environment and UI work one shared place to live.

#### Milestone 3 - Intent Layer

Status:
Complete for the first movement workflow.

Purpose:

Create the behavioural contract between simulation decisions and presentation performance.

Responsibilities:

- Derive short rolling intent queues from simulation state.
- Keep simulation authoritative for pathfinding, tasks, needs and world changes.
- Let Presentation consume intent continuously.
- Avoid exposing Intent directly to the renderer.
- Keep headless simulation independent.

Dependencies:

- Depends on Presentation World.

Implementation checklist:

- [x] `AgentIntent`
- [x] `IntentQueue`
- [x] Movement intent from simulation path state
- [x] Presentation-owned per-agent intent queues
- [x] Presentation movement consumes intent
- [x] Headless compatibility
- [x] Documentation
- [x] Tests
- [ ] Action intent
- [ ] Animation intent
- [ ] Social and mystery intent hooks

Completion criteria:

- Intent exists between Simulation and Presentation.
- Movement demonstrates the contract.
- Presentation can perform a walking intent through continuous presentation time.
- Simulation remains deterministic and authoritative.
- Renderer does not consume Intent directly.

Common mistakes to avoid:

- Do not turn Intent into a second AI planner.
- Do not schedule whole days of behaviour.
- Do not let Intent mutate gameplay state.
- Do not let the renderer query Intent directly.

Long-term architectural role:

Intent is the vocabulary Presentation uses to understand what villagers are trying to do. Future animation, idle life, celebrations, mysteries, companionship and cinematic camera work should observe Intent rather than reaching into gameplay internals.

#### Milestone 4 - Presentation Motion

Purpose:

Make visible movement continuous by performing Intent without changing discrete simulation movement.

Responsibilities:

- Consume movement intent.
- Maintain presentation path queues.
- Smooth target changes.
- Own facing interpolation.
- Prepare idle and animation hooks.

Dependencies:

- Depends on Presentation World.
- Depends on Intent Layer.
- Benefits from Observer Camera.

Implementation checklist:

- [x] Motion intent snapshots
- [x] Path queues
- [x] Continuous movement for walking intent
- [ ] Speed classes
- [ ] Easing profiles
- [ ] Motion blending when targets change
- [ ] Facing interpolation
- [ ] Idle behaviour hooks
- [ ] Animation state machine hook
- [ ] Sprite hooks
- [ ] Selection highlight follows presentation motion
- [ ] Tests

Completion criteria:

- Villagers no longer visually expose simulation ticks during ordinary movement.
- Movement still converges to authoritative simulation tile positions.
- Facing and selection presentation no longer snap unnecessarily.
- No pathfinding or movement gameplay rules change.

Common mistakes to avoid:

- Do not let presentation path queues create durable movement outcomes.
- Do not use smoothing to hide gameplay bugs.
- Do not turn speed classes into gameplay modifiers.

Long-term architectural role:

Presentation Motion turns intent into watchable motion. It is required before sprite animation can feel believable.

#### Milestone 5 - Presentation Environment

Purpose:

Move atmosphere and natural motion into Presentation time.

Responsibilities:

- Own weather presentation.
- Own cloud movement.
- Own wind phase.
- Own water animation.
- Own foliage animation.
- Own particle lifetime.
- Own lighting hooks.
- Own mystery visual presentation.

Dependencies:

- Depends on Presentation World.
- Should coordinate with Renderer Migration to protect terrain caches.

Implementation checklist:

- [ ] Presentation clock
- [ ] Weather presentation
- [ ] Cloud movement
- [ ] Wind
- [ ] Water animation
- [ ] Tree foliage
- [ ] Lighting hooks
- [ ] Particles
- [ ] Mystery presentation
- [ ] Seasonal visual interpolation where appropriate
- [ ] Tests

Completion criteria:

- Environmental presentation becomes independent of simulation tick timing.
- Weather, clouds, particles and mystery visuals no longer rely on `world.tick` as their long-term animation clock.
- Atmospheric effects do not invalidate terrain caches.
- Simulation exposes state and intensity; Presentation owns visual phase.

Common mistakes to avoid:

- Do not recolour or rebuild terrain for temporary atmosphere.
- Do not let weather particles imply gameplay effects the simulation did not create.
- Do not create one-off mystery, weather or foliage animation systems outside Presentation.

Long-term architectural role:

Presentation Environment makes the world feel alive even when villagers are still. It prepares the renderer for weather, wind, water, foliage, lighting and mysteries without gameplay refactors.

#### Milestone 6 - Renderer Migration

Purpose:

Gradually migrate renderer layers away from gameplay queries and toward Presentation Scene data.

Responsibilities:

- Define renderer layer contracts.
- Replace direct gameplay reads one layer at a time.
- Preserve cached terrain behaviour.
- Keep renderer stateless where practical.
- Keep simulation independent from rendering.

Dependencies:

- Depends on Presentation World.
- Should absorb Motion and Environment snapshots as those systems mature.

Implementation checklist:

- [ ] Terrain
- [ ] Roads
- [ ] Rivers
- [ ] Lakes
- [ ] Vegetation
- [ ] Structures
- [ ] Agents
- [ ] Weather
- [ ] Particles
- [ ] Selection
- [ ] UI
- [ ] Renderer layer contracts
- [ ] Direct gameplay-query reduction audit
- [ ] Tests

Completion criteria:

- Each migrated renderer layer consumes Presentation Scene data instead of gameplay objects.
- Renderer layer responsibilities are documented.
- Existing visuals are preserved during migration.
- Terrain cache behaviour remains stable.
- Renderer no longer decides what exists; it draws prepared presentation state.

Common mistakes to avoid:

- Do not rewrite all renderer layers at once.
- Do not duplicate gameplay state in snapshots.
- Do not allow renderer convenience to create new gameplay dependencies.

Long-term architectural role:

Renderer Migration is the final architectural conversion. It turns the renderer from a gameplay interpreter into a presentation compositor.

#### Milestone 7 - Visual Content

Purpose:

Replace debug-style visuals with a beautiful retro-inspired world after the Presentation architecture can support it.

Dependencies:

- Depends on Presentation World.
- Depends on Presentation Motion for characters.
- Depends on Presentation Environment for atmosphere.
- Depends on Renderer Migration for clean layer ownership.

Features:

- [ ] Pixel-art sprites
- [ ] Animated villagers
- [ ] Animated trees
- [ ] Animated water
- [ ] Wind effects
- [ ] Clouds
- [ ] Dynamic shadows
- [ ] Smoke
- [ ] Fire animation
- [ ] Weather particles
- [ ] Seasonal artwork
- [ ] Ambient environmental effects
- [ ] Lighting improvements
- [ ] Terrain polish
- [ ] Camera polish
- [ ] Post-processing experiments

Notes:

- The goal is atmosphere, not realism.
- The world should feel alive even when nothing important is happening.
- Players should want to leave the simulation running because it is beautiful to watch.
- Artwork should not arrive before the architecture can support it cleanly.
- Smoothness matters. Movement, weather, foliage, water, lighting, particles and camera motion should interpolate whenever possible.
- Visual features should enhance existing simulation state rather than invent gameplay facts.
- Presentation should support stories already produced by friendships, families, wanderers, mysteries, celebrations, memories, and the Chronicle.
- Prioritise readability and mood over visual density.
- Build reusable visual systems before creating large amounts of content.
- Reference Hyper Light Drifter and Stardew Valley only for presentation quality, movement, readability, atmosphere and colour confidence. Do not copy their art style.

Completion criteria:

- Sprites and effects consume Presentation state rather than gameplay objects.
- Visual content does not require gameplay refactors.
- Motion, animation, environment and camera systems remain presentation-owned.
- The world is more enjoyable to watch without making simulation less deterministic.

## Technical Debt

Purpose:

Track important engineering work without letting optimisation dominate the main story and presentation roadmap.

Tasks:

- [ ] Headless simulation performance
- [ ] Validation performance
- [ ] Renderer optimisation
- [ ] AI profiling
- [ ] Large-world performance
- [ ] Memory optimisation
- [ ] Simulation level-of-detail research for future large villages
- [ ] Renderer cache and layer profiling as sprite systems arrive

Notes:

- These remain important.
- They should support the living-world goal rather than replace it.
- Long-matrix validation throughput is future optimisation work, not a v0.8 release blocker.
- Large autonomous settlements remain a long-term ambition, but the immediate priority is story quality and atmosphere.
