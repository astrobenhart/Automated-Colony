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

v0.4 Smarter World is complete.

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

## Next Focus

v0.5 Settlement Simulation should focus on:
- roles as soft villager preferences
- settlement centers
- physical stockpiles
- clustered building placement
- local resource use around village hubs
- stronger long-term settlement behavior

Do not begin v0.5 by adding reproduction, migration, politics, warfare, or large-scale economy. The next step is making stable shelter clusters become recognizable early villages.

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
