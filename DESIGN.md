# Automated Colony Simulation

## Core Concept

A world simulation where the player creates a world and watches autonomous agents survive, explore, build, cooperate, compete, and create history.

The player does not directly control units.

The goal is emergent storytelling through simulation.

## Core Loop

Need
→ Goal
→ Target
→ Movement
→ Action
→ World Change
→ Event

## Current Architecture

v0.5 Colony Roles and Production is complete.

Agents should:
- remember resources
- pathfind
- choose goals
- survive longer

World generation should:
- use centralized settings for reproducible and tunable worlds
- create deterministic worlds when given a seed
- generate elevation, moisture, and temperature maps
- trace simple downhill rivers from high elevation toward lower elevation
- assign water, mountain, hill, forest, wetland, dry, plain, and grass terrain from simple natural rules
- place food and wood based on terrain conditions
- apply terrain and season based resource growth, caps, and gradual die-off
- create rare visible environmental events such as drought and heavy rain
- record major environmental events in persistent world history
- spawn ambient wildlife from biome suitability without adding hunting or combat
- cycle simple seasons that influence terrain-based resource regrowth
- tint terrain by season in the renderer, blending during the final day, without changing gameplay tile kinds
- preserve existing simulation systems while preparing for biomes and environmental events

World generation settings should:
- keep defaults compatible with normal gameplay
- validate or clamp unsafe values
- expose seed, size, water level, forest density, and climate harshness
- support presets such as normal, wet, dry, forest, and harsh
- remain internal and preset-driven for now, without a player-facing setup screen

World identity should:
- be generated from actual terrain, resource, wildlife, and settings conditions
- give each world an evocative title, compact subtitle, and estimated survival outlook
- keep hidden tags for future history, settlement, and storytelling systems
- make the player feel they are discovering a world rather than configuring one

World history should:
- remain separate from the short-term event log
- store structured permanent entries for major events
- start with environmental history
- leave wildlife, settlement, migration, lineage, ruins, and myth history for later milestones

UI should:
- keep current simulation and colony status visible at a glance
- prefer compact grouped sections as more systems are added
- preserve selection, active events, history, legend, controls, and recent event visibility without changing simulation behavior
- keep the default right panel player-facing, with debug-style internals reserved for selected-object details
- use role-based villager colors as gameplay readability, so Generalists, Foragers, Builders, and Scouts can be identified without clicking them
- show the village's discovered resource knowledge rather than perfect food/wood information

## Next Focus

v0.5 is the stable settlement-economy foundation.

The next roadmap work should build from the completed v0.5 village behavior without adding player micromanagement.

The v0.6-v0.9 progression should make villages feel alive without making them fragile, noisy, or broken:
- v0.6 should add individuality without adding population collapse.
- v0.7 should add migration as the first renewal/expansion mechanism.
- v0.8 should add rare Mysteries and Wanderers after villagers and settlements can react and remember.
- v0.9 should synthesize settlement, migration, memory, ruins, and major events into long-term history.

Future directions include deeper logistics, migration/new settlements, social simulation, roads, richer farming, and rare Mysteries and Wanderers. Do not begin the next milestone by adding politics, warfare, large-scale economy, or player work-order systems.

Resource Reservation v1 is the current coordination layer. Full hauling and job assignment remain future logistics work and should not be tied to v0.6. Logistics should be introduced only when there are enough production chains and destinations to justify the added complexity.

## Stable Living Villages

The simulation should prioritize continuity over novelty.

A small number of meaningful long-term events is preferable to many frequent events.

Systems should build on existing history whenever possible.

Core stability principle:
- Do not add a new death source before adding a renewal source.
- Do not introduce old-age death before reproduction, migration, or new arrivals exist.
- Age in v0.6 is identity/story, not attrition.
- Villagers should feel more individual without causing guaranteed village extinction.
- Social systems should add flavor, memory, and identity before they add churn.
- Survival needs remain dominant over social behavior.

v0.6 life and social foundations should focus on labels and lightweight flavor:
- Adult and Elder can be lifecycle labels.
- Elders may move slower, work less often, influence leadership/memory/history, or appear more often in notable events.
- Elders should not automatically die of old age until a renewal system exists.
- Traits, mood, morale, familiarity, leadership, mourning, and pair/family labels should remain lightweight.
- Reproduction, children, inheritance, full family trees, and old-age death remain deferred.
- Lifecycle Labels v1 is intentionally static identity metadata. Villagers are assigned Adult or Elder when created, the label appears in selected-villager details, and there is no Adult-to-Elder progression or Elder-to-death rule.

Traits should describe villagers before they influence villagers.

Trait phases:
- Phase 1: Traits create identity.
- Phase 2: Traits may influence mood.
- Phase 3: Traits may influence relationships.
- Phase 4: Traits may influence behavior.

Simple Traits v1 implements Phase 1 only. Each villager receives one static display-only trait at creation. Traits appear in selected-villager details and do not affect movement, pathfinding, exploration, gathering, building, workshop use, farming, survival needs, recovery, roles, goals, settlement needs, reservations, or carrying capacity.

## State Labels

State = what the villager is doing or experiencing now.

Mood = how the villager feels.

Only State exists currently. Mood, morale, emotional memory, mood meters, relationship-driven feelings, and emotional systems remain future work.

State Labels v1 are computed from existing villager data such as hunger, thirst, fatigue, current action, current goal, recovery, rest, work, and exploration. State is shown in selected-villager details alongside Role, Life, and Trait.

State labels are descriptive only. They do not affect goal selection, pathfinding, gathering, building, farming, workshops, exploration, role behavior, survival behavior, reservations, carrying capacity, traits, or lifecycle labels.

## Social Memory and Familiarity

Social memory records repeated shared presence.

Familiarity is not friendship.

Social systems should be observational before behavioral.

Social Memory v1 tracks villagers who spend repeated days near one another. Familiarity grows slowly through neutral labels: Stranger, Seen, Acquainted, and Familiar.

The selected-villager UI may show a compact familiarity summary such as `Knows: Bryn (Familiar)`.

Stored social-memory data can support future systems such as leadership, mourning, migration, history, mysteries, and relationships, but it has no gameplay effect yet.

Social memory does not affect goals, pathfinding, gathering, building, farming, workshops, exploration, survival, reservations, carrying capacity, state labels, role behavior, traits, or lifecycle labels.

## Influence Foundation

Influence is soft social importance.

Influence is not leadership.

Influence is not command authority.

Influence emerges from being known, remembered, and familiar to others.

v0.6 Influence Foundation computes a current Influence label from recent incoming social familiarity. Stronger familiarity counts more than weak familiarity, stale memories can stop contributing to current influence, and only the strongest few incoming relationships are counted so raw familiarity does not automatically flatten every long-lived villager to the same score.

Current Influence labels are Low, Emerging, Notable, and Respected. These labels are observer-facing only and appear in the Villagers overlay details pane.

Villagers also store peak influence score as future-facing metadata for history, mourning, migration, mysteries, former leaders, legends, and major events. Peak influence does not affect behavior.

Influence does not affect goals, pathfinding, gathering, building, farming, exploration, role behavior, state labels, mood/morale, social familiarity growth, survival, settlement decisions, reservations, or migration.

Future formal leadership should build on influence without becoming volatile. Influence should remain dynamic. Leadership should remain stable. Future leaders should generally remain leaders until death or a major exceptional event, and succession should happen primarily after death.

Raw familiarity can eventually flatten if everyone knows everyone. Future systems may need recency weighting, decay or staleness, relative ranking, top-relationship weighting, and meaningful relationship caps to keep social importance differentiated over long simulations.

## Overlay Framework

The right panel remains compact.

Detailed information moves into focused overlays.

Overlays are observer tools, not command tools.

Overlay Framework v1 uses pygame-gui to support reusable, closable, draggable inspection windows without adding player commands or changing simulation behavior.

Villagers is the first overlay. It uses a master/detail layout with a living-villager list on the left and selected-villager details on the right. Selecting a villager from the map or overlay updates the same selected-villager state.

The Villagers overlay is the primary villager inspection interface. The right panel remains focused on world identity, time, colony status, resources, active events, selection summary, history, controls, and recent events.

Villager details use an RPG-style character card. The card prioritizes identity and story: portrait, name, role, lifecycle stage, trait, high-level State, Influence, and familiar villagers.

Fast-changing telemetry is intentionally excluded from the character card. Raw hunger, thirst, fatigue, carried inventory counts, path data, target data, and internal counters belong in tests or future debug tools, not in the primary villager profile.

Future overlays such as Settlements, History, Wildlife, Visitors, Mysteries, and Ruins should plug into the same overlay manager instead of becoming one-off windows.

## Appearance System

Appearance System v1 adds stable identity metadata:
- `appearance_seed`
- `appearance_type`

Villager character sprites are generated procedurally from appearance metadata. They are deterministic, lightweight, and do not require an external art pipeline.

Character sprites use a simple layered architecture:
- outline
- base / skin
- hair
- eyes
- body
- clothing
- accent pixels

The first sprite consumer is the Villagers overlay. The selected villager shows a crisp full-body pixel-art sprite generated at low resolution and scaled up with nearest-neighbor scaling.

The sprite style is inspired by compact Game Boy Color-era RPG character presentation without copying specific sprites, characters, palettes, or assets.

Sprites reflect appearance, lifecycle stage, and role color:
- appearance controls skin tone, hair color, hair style, face shape, and eye placement
- elders use grey / white hair
- clothing uses the same role colors used for villagers on the map

Sprites are identity and presentation only. They do not affect AI, roles, traits, lifecycle behavior, state labels, familiarity, influence, resources, pathfinding, romance, family, reproduction, or inheritance.

Future layers may add hats, cloaks, beards, walking sticks, accessories, scars, blessings, founder markers, mystery effects, or historical markers without replacing the base appearance system.

## Resource Knowledge Rendering

The world is visible. Resource abundance is discovered.

The player sees the village's discovered resource knowledge, not perfect resource information. Terrain remains fully visible: plains, grassland, forests, wetlands, rivers, lakes, hills, mountains, and seasonal terrain changes are not hidden or darkened.

This is resource-knowledge rendering, not fog-of-war.

Rendering rules:
- Wild food markers and quantities appear only when the tile is in colony memory as known food.
- Wild wood markers and quantities appear only when the tile is in colony memory as known wood.
- Unknown resource tiles still render their underlying terrain.
- Forest terrain remains visible even when harvestable wood on that forest tile is unknown.
- Farms, stockpiles, shelters, workshops, the settlement center, villagers, and wildlife remain visible.
- Colony memory is the source of truth for resource visibility.

## Role-Based Resource Discovery

Role-based discovery exists to influence colony knowledge growth.

It should not become a critical survival dependency.

A colony without scouts should still function. Scouts accelerate discovery rather than enabling discovery.

Discovery rules:
- Scouts discover the most across food, wood, and water.
- Foragers are naturally better at discovering food and water.
- Generalists remain broadly capable.
- Builders remain locally aware, especially around wood, and should not feel blind.
- Discovery uses simple radius checks centered on the villager.
- There are no view cones, directional vision, line-of-sight, raycasting, BFS, or pathfinding in discovery.
- Personal memory and colony memory sharing remain the discovery output.

v0.7 migration should provide the first renewal and expansion path:
- Food pressure can lead to farming.
- Population pressure can lead to migration or a new settlement.
- A small group may decide to leave, travel or abstractly depart, and found or record a new settlement.
- Migration should not require deep family trees, diplomacy, politics, warfare, or a full economy first.

Mysteries are more powerful once villagers and settlements can remember and react:
- A wizard is more interesting when villagers can gather, fear, admire, remember, or be changed by the event.
- Rare surprises should feel emergent, not player-triggered.
- The user observes; the world unfolds; villagers act autonomously.
- The player should not summon visitors or know every possible surprise.

## Roles

Villagers are survivors with preferences, not workers with fixed assignments.

Implemented roles:
- Generalist: no specialty modifier
- Forager: modest preference for food gathering and food storage
- Builder: modest preference for wood gathering and shelter building
- Scout: modest preference for exploration

Role rules:
- roles modify goal utility only when immediate needs are reasonably satisfied
- thirst, hunger, and fatigue remain dominant
- no role is mandatory for colony function
- there is no player role assignment, job board, task claiming, or micromanagement
- role colors are intentionally high contrast and player-facing, because watching the colony should reveal what villagers are doing without requiring selection

## Settlement Center v1

The settlement center is a conceptual village anchor, not a full building system.

Implemented behavior:
- each world has one settlement
- the settlement is automatically founded before villagers spawn
- the founding tile is selected near the map center using bounded suitability scoring
- the exact center is not forced; nearby valid terrain is chosen when the center is blocked or poor
- villagers spawn afterward in a small deterministic cluster around the settlement center
- the center is placed on walkable terrain
- the settlement has a deterministic short name connected to the generated world identity
- it tracks founding day, founding season, living population, and radius
- the right panel and map marker make the settlement visible

Non-goals for v1:
- no player placement
- no setup screen
- no physical stockpile tile
- no hauling jobs
- no task claiming
- no migration or multiple settlements
- no forced villager destination behavior

Future systems can use the center as the origin for local work radius, clustered building placement, physical storage, village identity, expansion, and settlement history.

## Village Hub Behavior v1

The settlement center influences routine behavior but does not command villagers.

Implemented behavior:
- calm wandering prefers random walkable tiles near the settlement instead of pure local drift
- role preferences affect local range: builders and foragers stay closer, generalists use the settlement radius, scouts can range farther
- shelter construction prefers valid grass build sites inside the settlement radius before falling back
- settlement activity records where villagers spend time in a lightweight heatmap

Survival remains dominant:
- thirst still drives drinking and water seeking
- hunger still drives eating and food seeking
- fatigue still drives shelter and sleep behavior
- there is no mandatory return-to-settlement goal

Future systems can use activity heat to suggest roads, stockpile locations, workshops, districts, and village expansion pressure.

## Physical Stockpiles v1

Physical stockpiles make the village economy visible without replacing shared storage.

Implemented behavior:
- each settlement creates one food stockpile and one wood stockpile near the settlement center
- stockpiles are walkable map markers, not terrain types
- villagers carrying extra food or unused wood seek adjacent stockpile access tiles before depositing
- deposits update both `ColonyStorage` and the visible stockpile amount
- eating from storage still uses abstract `ColonyStorage`

Design boundaries:
- `ColonyStorage` remains the source of truth
- stockpiles do not reserve resources
- villagers do not withdraw from specific piles yet
- no hauling jobs, workshops, farms, roads, or task claiming are introduced

Future systems can turn stockpiles into foundations for hauling, workshops, farms, resource chains, local shortages, and settlement logistics.

## v0.5 Production Sequence

v0.5 production should progress from visible storage to simple workshops before full hauling logistics.

Reasoning:
- stockpiles make settlement resources physically visible
- workshops give stored resources a productive use
- builders need meaningful village-local work before a larger logistics system exists
- hauling and task claiming should wait until there are enough resource destinations to justify the added complexity

This keeps the simulation hands-off while gradually making the village economy more legible and useful.

## Workshop v1

Workshop v1 makes stockpiled resources useful without adding a logistics layer.

Implemented behavior:
- each settlement creates one basic workshop near the village hub
- the workshop is a visible map marker, not a terrain type
- calm Builders can seek and work adjacent to the workshop
- workshop progress converts stored wood into building materials
- building materials reduce shelter wood cost when available
- shelter construction still works normally without building materials

Design boundaries:
- workshop work is autonomous and optional
- survival needs remain dominant
- the workshop consumes from shared storage directly
- no hauling, reservations, production menus, crafting queues, farming, roads, or player placement are introduced

Future systems can use workshops as destinations for hauling, production chains, building upgrades, and specialist roles once the simulation has enough resource flow to justify task claiming.

## Settlement Needs v1

Building priorities are now settlement-level needs rather than independent builder-only decisions.

Implemented behavior:
- each settlement tracks simple need scores for shelter, wood, and materials
- needs are updated centrally from population, shelter capacity, colony storage, and workshop availability
- the top need uses simple thresholds and hysteresis to avoid obvious oscillation
- Builders respond to the top settlement need when thirst, hunger, and fatigue are under control
- shelter need drives shelter construction when capacity is short
- wood need drives wood gathering when construction or material production lacks wood
- materials need drives workshop use when wood exists and the material buffer is low
- workshop work slows/stops once the material buffer is full

Design boundaries:
- no job board
- no construction queue
- no hauling or task claiming
- no roads
- no player placement
- no zoning

Thresholds are intentionally conservative and tunable. This is the first step toward settlement-level decision making, not a logistics system.

## Resource Reservation v1

Reservations are soft coordination, not a job system.

Implemented behavior:
- the world owns a small reservation manager
- agents can reserve food tiles, wood tiles, shelter build sites, and workshop use
- target selection prefers unreserved food and wood when alternatives exist
- clustered build placement skips build sites reserved by other builders
- workshop reservations keep every Builder from crowding the same workshop at once
- reservations expire after a short timeout
- reservations release on completion, target invalidation/depletion, death, or no-progress recovery
- critical hunger can override food reservations if no alternative food is available

Design boundaries:
- no job board
- no task queue
- no hauling chain
- no item stacks on the ground
- no inventory reservations
- no player work orders

Full hauling and task claiming should build on this later, after the simulation has more destinations and resource chains.

v0.5 uses Resource Reservation v1 as lightweight coordination. It prevents duplicate effort without adding a full job board or hauling system. Full hauling/logistics will be revisited once farming, production chains, or multiple resource destinations justify it.

## Farming v1

Farming is autonomous settlement support, not player placement or full agriculture.

Implemented behavior:
- settlements create 2x2 `FarmPlot` objects only when food pressure is high
- food pressure becomes HIGH when effective food is at or below 1.5 days of population, MEDIUM at or below 3 days, and LOW above that
- effective food counts stored food, ready farm food, and a bounded amount of local wild food so normal foraging can delay farms
- the first farm can be created from the first daily farming check on day 2 or later, never directly during settlement founding
- sustained high pressure creates at most one farm per day until the population-based cap is reached
- each farm plot owns exactly four tiles and is tracked by the settlement
- farm placement uses bounded local scoring near the settlement hub
- placement avoids water, mountains, stockpiles, workshops, shelters, agents, existing farms, and the settlement center
- placement scoring uses cheap terrain, distance, openness, water proximity, and special-tile proximity checks without pathfinding
- farms grow once per day, with Spring/Summer/Autumn growth and much slower Winter growth
- drought reduces farm growth and heavy rain improves it through the existing environmental event model
- ready farms can be harvested through the existing food goal
- Resource Reservation v1 can reserve a farm plot while a villager is moving to harvest it
- critical hunger can still override farm reservations when no alternative exists
- farm plots render as terrain-like interiors with a brown outline around the whole 2x2 plot

Design boundaries:
- no player farm placement
- no farming setup UI
- no crop selection, seeds, irrigation, or soil simulation
- no roads or zoning
- no full hauling or job board
- no farms at settlement founding unless future balance rules explicitly create food pressure before the first daily check

Farming should stabilize long-term survival without making wild foraging, winter storage, or environmental pressure irrelevant.

## Settlement Carrying Capacity v1

Carrying capacity is a readable settlement pressure report, not a hard population limit.

Implemented behavior:
- settlements keep a `CarryingCapacityReport`
- the report shows living population, estimated capacity, status, one primary reason, and detailed reason lines
- capacity is the lowest current support estimate across shelter, food, and water
- shelter support comes from built shelter capacity
- food support comes from stored food, local wild food, ready farm food, and active farm plots
- water support comes from local known water access
- the renderer uses the report for a short colony status and capped reason lines
- the default panel shows population as plain villager count, such as `9 Villagers`, and does not display capacity as a max denominator

Design boundaries:
- no population growth
- no migration
- no hard population cap enforcement
- no player controls
- no new job system or logistics layer

The goal is to make settlement problems legible at a glance. If the panel says `Food Strained`, it should also explain the food/storage/farm context that caused that status.

## Right Panel Summary v1

The right panel is a player-facing observation dashboard.

Implemented behavior:
- world identity remains the top anchor
- Day, Year, Season, and Speed appear in a compact two-row grid below the identity
- the separate debug-style Simulation section is removed from the default summary
- Colony shows villager count, settlement status, stored food/wood, farm count, and building materials
- strained colonies show at most three short reason lines
- stable colonies keep the main summary compact and omit reason lines
- detailed values such as settlement center, radius, claims, farm growth, farm food, workshop progress, and capacity estimate live in selected-object details

Design boundaries:
- no gameplay logic changes
- no model data removal
- no population current/max display
- no menus or renderer overhaul

The default panel should answer what world this is, what time it is, how the colony is doing, and what just happened.

## Mysteries and Wanderers

The project is evolving beyond a resource simulation.

It is becoming a living world that the player watches.

Because the project has a strong screensaver / ant-farm quality, the simulation should occasionally create moments where the observer thinks:

`Wait... what is THAT?`

Those moments should be rare, memorable, and partly unexplained.

Core principle:
- the player should not know every possible surprise
- the world should occasionally produce strange, rare, mysterious, magical, or unexplained events without player control
- these events exist to generate stories
- they are not another management layer
- they are not RPG mechanics
- they do not replace colony survival, settlement, production, or ecology

### Screensaver Principle

The project is partly a simulation and partly a living screensaver.

Rare events should occasionally create moments that make the observer stop and watch. The simulation should be capable of surprising the player even after many hours.

The player does not summon these events. The player does not command them. The world produces them.

### Rare Visitors

Visitors are unusual autonomous entities, not normal villagers.

Possible visitors:
- Wandering Wizard
- Strange Hermit
- Lost Knight
- Travelling Merchant
- Dreaming Pilgrim
- Golden Stag

Visitor rules:
- rare means rare
- visitors arrive and leave
- visitors should feel unusual
- visitors should not become colony roles
- visitors should not become player-controlled units
- visitors should not create a job board, quest system, or new management layer
- villagers may react autonomously, but survival needs should remain important

### Strange Events

Possible examples:
- Meteor Strike
- Falling Star
- Aurora
- Ghost Lights
- Singing Forest
- Sudden Mist
- Animals gathering silently at night

These are examples only. The final list should remain intentionally open so the observer cannot memorize every possible surprise.

Events should be bounded. They should not happen constantly. They should not dominate survival systems. Some mystery should remain unexplained.

### Mysteries and Landmarks

Possible examples:
- Ancient Standing Stone
- Hidden Ruin
- Crystal Spring
- Sleeping Giant Tree
- Marked Grove
- Forgotten Shrine

Mysteries and landmarks may appear through world generation, rare events, or visitor interactions. They should make the world feel older and stranger than the colony. Some may have small effects; some may simply be remembered places.

### Wandering Wizard Example

Day 217:

A wizard appears at the edge of the map.

Villagers begin gathering around him.

Nobody knows why.

Several days later the wizard leaves.

Possible outcomes:
- crop growth improves temporarily
- a water source is revealed
- one villager becomes a Dreamer
- a standing stone appears
- a blessing or curse affects a small area

The exact effect should remain somewhat mysterious. The wizard is one possible visitor, not the entire system.

### Future Architecture Notes

Prefer generic systems rather than a hardcoded wizard.

Possible future modules:
- `visitors.py`
- `mysteries.py`
- `magical_events.py`

Possible future concepts:
- `Visitor`
- `MysteryEvent`
- `MagicalEffect`
- rare spawn scheduler
- bounded duration
- history integration
- villager reaction hooks
- renderer markers

Mysteries should integrate with world history so the world remembers that something happened, without always explaining why.

Design boundaries:
- do not add player summoning
- do not add player commands for visitors
- do not add a spell system
- do not add RPG quests
- do not make effects frequent or dominant
- do not let mystery systems replace survival, ecology, production, or settlement simulation
- keep some things unexplained

## Local Resource Radius v1

The settlement has a soft resource territory, not an invisible wall.

Implemented behavior:
- settlements track a local resource radius and expanded resource radius
- food, wood, and water pressure are estimated as LOW, MEDIUM, or HIGH
- agents prefer reachable local resources under low pressure
- agents expand to the larger radius when local resources or storage are strained
- urgent hunger and thirst can use any reachable known resource
- scouts receive a weaker local penalty and can range farther
- foragers and builders retain stronger preferences for local food and wood

Design boundaries:
- no player-controlled territory
- no zoning
- no roads
- no hauling or task claiming
- no hard boundary that can trap villagers into avoidable starvation or thirst

The radius should make the village feel like it has a work territory while still allowing expansion when scarcity demands it.

## Clustered Building Placement v1

Clustered placement is an autonomous helper system, not player zoning.

Implemented behavior:
- `src/building_placement.py` answers where a nearby building should go
- shelter construction prefers scored sites near the settlement hub
- scoring uses distance to the hub, spacing from existing shelters, stockpile/workshop proximity, open neighbors, and cheap access-preservation checks
- shelters prefer loose clusters instead of solid shelter blobs
- if no ideal local site exists, builders can still fall back to broader bounded settlement-area placement or existing nearby build behavior

Performance boundaries:
- no pathfinding in build-site scoring
- no flood fill
- no full zoning or road planning
- no player-directed placement
- no hauling, reservations, task claiming, or multiple settlements

Future building types can reuse the same helper, but full roads, districts, and stronger settlement planning should come later.

## Settlement Arc

The long-term simulation arc is:

Survivors -> Colonists -> Villagers -> Settlements -> Historical Societies

Current behavior:
- Villagers naturally cluster near shelters.
- Exploration is mostly local.
- Colonies often suffer early population loss before stabilizing.
- Stable colonies tend to remain in a small area.

Desired future behavior:
- Shelter clusters become recognizable villages.
- Villages form around settlement centers.
- Storage, shelters, and production buildings cluster near local hubs.
- Villagers prefer nearby resources before ranging farther out.

Long-term behavior:
- Resource scarcity, population pressure, and social conditions can drive expansion.
- Some groups may migrate or form splinter settlements.
- Settlements can gain names, identities, founding dates, notable events, lineages, and ruins.
- Multiple settlements should emerge from simulation pressure rather than scripted history.

Non-goals for the current roadmap:
- Warfare
- Diplomacy
- Economy
- Politics
- Kingdoms

These may become future possibilities, but the next design step is village formation, not large-scale states.

## Design Priorities

1. Emergence over scripting
2. Simulation over graphics
3. Readability over realism
4. Small systems that interact
5. Observable behavior
