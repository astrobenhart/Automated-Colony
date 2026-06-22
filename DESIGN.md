# Automated Colony Simulation

## Core Concept

A slow autonomous settlement screensaver where villagers live, work, age, reproduce, die, remember, inherit traits, and gradually change the land around them, while natural forces also reshape the world.

The player does not directly control units.

The goal is emergent storytelling through long-running settlement simulation.

The world should feel lived in. The player should feel like they are observing a place with homes, paths, jobs, routines, households, children, elders, births, deaths, inherited traits, memories, history, land changed by people, and land changed by natural forces.

The settlement should not feel like a blank map where every villager starts from scratch. The player is not founding every story. The player is arriving partway through ongoing village life.

Automated Colony is not a colony manager. The observer watches the world unfold; they should not assign every job, command households, place every building, or run a work-order board.

## Core Loop

Need
→ Goal
→ Target
→ Movement
→ Action
→ World Change
→ Event

## Current Architecture

v0.6 Villager Life and Social Foundations is complete.

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

v0.7 should establish the lived-in settlement foundation.

The next roadmap work should build from the completed v0.5 settlement economy and v0.6 social identity systems without adding player micromanagement.

The future progression is:
- v0.7: lived-in settlement foundation.
- v0.8: generations and household life.
- v0.9: workplaces, professions, and delivery networks.
- v1.0: large autonomous settlement screensaver.

Preserve compatible earlier ideas as future systems: migration, splinter settlements, ruins, mysteries, wanderers, deeper logistics, and multi-settlement history still matter, but the immediate direction is a village that already feels inhabited.

Resource Reservation v1 is the current coordination layer. Full hauling and job assignment remain future logistics work. Logistics should be introduced only when homes, workplaces, roads/paths, production chains, and destinations justify the added complexity.

## Lived-In Place Principle

The simulation should prioritize continuity over novelty.

A small number of meaningful long-term events is preferable to many frequent events.

Systems should build on existing history whenever possible.

The world should feel like it existed before the player arrived. The default start should eventually be a village already in progress, not a bare wilderness map where all social memory, buildings, routines, and history begin at zero.

Starting village fabric may include:
- homes
- farms
- storage
- workshops
- workplace placeholders
- paths
- households
- villagers with roles
- villagers with ages/lifecycle stages
- villagers with social bonds
- remembered dead
- existing Chronicle entries
- fields and paths showing prior human activity

Starting scenarios:
- Frontier Camp: closest to the current experience, with 10-20 villagers, fewer buildings, and visible survival pressure.
- Small Village: recommended v0.7 default, with 30-60 villagers, homes, farms, paths, workplaces, simple households, existing routines, and social bonds.
- Old Village: future scenario with established history, remembered dead, worn paths, older buildings, and larger family networks.
- Market Town: future scenario with 100-200 villagers, districts, more professions, and delivery networks.

Current v0.7 Phase 1 implementation:
- The default start uses the existing central settlement founding logic, then places 8-15 visible home tiles in a loose cluster inside the village radius.
- The default population is 45 villagers, within the short-term 30-60 villager target.
- Villagers spawn on a randomly assigned home tile or an adjacent valid tile after homes are created.
- Multiple villagers can share a tile. Spawning and core movement do not enforce one-agent-per-tile occupancy.
- This phase does not seed paths, farms, storage expansion, history, social familiarity, schedules, households, reproduction, or delivery systems.

## Stable Living Villages

Core stability principle:
- Do not add a new death source before adding a renewal source.
- Do not introduce old-age death before reproduction, migration, or new arrivals exist.
- Villagers should feel more individual without causing guaranteed village extinction.
- Social systems should add flavor, memory, and identity before they add churn.
- Survival needs remain dominant over social behavior.
- Generation systems should support continuity, not erase scarcity.

v0.6 life and social foundations remain lightweight:
- v0.6 introduced Adult and Elder as lifecycle labels.
- Traits are currently display-first.
- Social memory, influence, remembrance, settlement identity, and social bond labels are observer-facing.
- Lifecycle Labels v1 was static identity metadata. Villagers were assigned Adult or Elder when created, the label appeared in selected-villager details, and there was no Adult-to-Elder progression or Elder-to-death rule.

v0.7 mixed starting population:
- Starting villagers now receive seeded ages, lifecycle stages, and experience labels.
- Lifecycle stages are Young Adult, Adult, Older Adult, and Elder.
- Experience labels are Novice, Experienced, and Veteran.
- Household founding years and established-years metadata imply village history before observation begins.
- These fields are still static startup metadata; there is no aging progression, child stage, old-age death, reproduction, or inheritance logic yet.

v0.7 should not implement reproduction casually. It should prepare the settlement model, start generation, and identity/history layers so reproduction, children, parent links, inherited traits, and aging can arrive as coherent systems later.

## Daily Life Model

Daily routines should become a core simulation unit.

Villagers should eventually have slow, readable rhythms:
- wake
- eat
- go to workplace
- work
- rest or socialize
- return home
- eat
- household time
- sleep

A complete in-game day may eventually take several real-world hours in screensaver mode. The goal is not speed. The goal is watchable continuity.

Future-facing example:

A blacksmith wakes early, walks to the forge, starts the forge, receives raw materials, crafts goods, sends goods into storage or delivery networks, closes the forge, returns home, eats, spends time with household, sleeps, and wakes again the next day.

This blacksmith sequence is aspirational future behavior, not a v0.7 acceptance requirement.

Current Daily Schedule Foundation:
- the village uses one shared settlement clock phase: Morning, Day, Evening, or Night
- phase boundaries vary by season while the overall daily tick budget remains stable
- Morning releases villagers from home/sleep states so planner work can resume
- Day leaves the settlement planner and persistent task execution in control
- Evening prevents idle villagers from starting fresh routine work and sends them toward home or the village center
- Night strongly sends villagers home and keeps them sleeping or resting there
- critical hunger, thirst, and fatigue remain survival overrides and may interrupt any phase
- household/home assignments provide the night anchor, so household members naturally gather at shared homes
- the right panel displays the current phase beside Day, Year, Season, and Speed

Design boundaries:
- no individual schedules
- no weekly, seasonal, or profession-specific calendars
- no player scheduling controls
- no change to task frequency or per-villager decision cadence

Current Day Progress HUD:
- the right panel uses a dedicated Time header as the primary visual representation of the day
- Season appears first, followed by a segmented day progress bar, current phase, and Year/Day/Speed context
- the progress bar uses the same seasonal phase boundaries as villager behavior, so Summer shows longer daylight and Winter shows longer night
- the bar is lightweight immediate-mode UI rendering and does not touch world simulation state
- future weather, temperature, storm, drought, and event badges should be added to this Time header rather than creating another competing top-level dashboard

## Paths and Lived-In Land

Paths are a major design pillar because they visually communicate that people live here.

v0.7 may begin with:
- pre-generated village paths
- simple worn-path tiles
- paths between homes, farms, storage, and workplaces

Future versions may add:
- path wear from repeated travel
- road improvement
- abandoned paths fading
- paths around ruins or old homes

The screensaver experience depends on seeing the land accumulate history.

The land should be changed by both villagers and natural forces.

Natural forces may include:
- seasons
- drought
- heavy rain
- vegetation changes
- wildlife movement
- water/river changes eventually

Human forces may include:
- paths
- farms
- cleared woods
- buildings
- workshops
- storage
- worn ground
- abandoned homes
- ruins
- expanded fields

## Households and Reproduction Direction

Households are the bridge between current villager identity and future reproduction.

Households should eventually represent:
- shared home
- partners
- children
- elders
- relatives or companions
- people who eat, sleep, and live together

v0.7 can begin with household foundations without full reproduction.

Households are the conceptual home for reproduction, children, inherited traits, family history, births, deaths, and long-term continuity.

Do not add:
- complex inheritance law
- family tree UI
- romance simulation
- detailed domestic economy
- player household assignment

Reproduction should be part of the long-term simulation direction, but it should not be a simple population counter.

Future reproduction should be tied to:
- households
- lifecycle
- identity
- traits
- Chronicle/history
- settlement capacity/pressure
- long-term population continuity

Future systems should support:
- partners or reproductive households
- children
- parent links
- inherited traits
- aging from child to adult to elder
- birth events
- family history
- death and remembrance across generations

Trait inheritance direction:
- a child may inherit one trait from one parent
- a child may blend tendencies from both parents
- there may be a small chance of a new/random trait
- traits should remain simple and display-first before deeply changing behavior

## Simulation Scale and Level of Detail

Target scale:
- short-term v0.7: 30-60 villagers
- medium-term: 100-200 villagers
- long-term: hundreds of villagers

The architecture must avoid full expensive per-tick simulation for every villager.

Simulation level of detail should eventually support:

Visible / nearby villagers:
- detailed movement
- current task/state
- animation
- local interactions
- pathfinding

Offscreen / less relevant villagers:
- simplified schedule state
- approximate location
- work progress
- resource consumption/production

Background villagers:
- hourly/daily summaries
- social updates
- births/deaths
- work completion
- history events

This is required to support hundreds of villagers without performance collapse.

## Deferred Boundaries

The long-term vision may include richer work, families, logistics, and towns, but keep these out of v0.7:
- full blacksmith production chain
- full delivery/logistics network
- full economy
- full family tree UI
- pregnancy mechanics
- inheritance law
- romance drama
- politics
- formal leaders
- multi-settlement trade
- hundreds of fully pathfinding villagers
- micromanagement UI
- player job assignment
- work orders

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

## Death Memory and Remembrance

Death should create memory and history before it creates mechanics.

Deaths should feel like remembered events in village history rather than temporary status effects, morale penalties, or productivity failures.

Death Memory v1 has three conceptual layers:
- Death Record: permanent history.
- Remembrance: temporary social memory.
- Legacy: future system.

Only Death Record and Remembrance exist currently.

Death Records are permanent identity snapshots created when a villager dies. They preserve name, villager id, role, lifecycle stage, trait, appearance metadata, cause of death, day, season, year, current influence label, peak influence label, and the villagers who remembered them.

Death Records do not rely on the living villager object continuing to exist.

Each villager should create exactly one Death Record.

Remembrance is temporary and personal. Villagers who were meaningfully familiar with the dead may show a compact line such as `Remembering: Rowan` in villager inspection. Remembrance is not a generic Mourning state.

Only meaningful relationships should create remembrance. Familiar villagers can remember the dead; strangers and villagers who only saw them once should not cause colony-wide remembrance.

Remembrance is flavor only. It does not affect goals, pathfinding, gathering, building, farming, exploration, role behavior, state labels, social familiarity growth, influence, survival, productivity, morale, or carrying capacity.

Legacy remains future-facing. The preserved death data may later support former leaders, founders, respected elders, migration stories, remembered dead, settlement history, ruins, legends, or mysteries, but those systems are not implemented in Death Memory v1.

## Settlement Identity and Belonging

Settlement membership should create belonging before it creates politics.

Settlement Identity v1 is informational only. It gives villagers a stable home settlement identity so character cards, death records, and Chronicle entries can refer to where a villager belongs.

v0.6 implementation:
- villagers receive `home_settlement_id` and `home_settlement_name`
- villagers also store future-facing `birth_settlement_id` and `birth_settlement_name`
- starting villagers belong to the starting settlement
- villager character cards show a compact `Home` row
- death records preserve settlement identity
- death-history and Chronicle wording can say `Rowan of Oakvale` when the data is available

Settlement identity does not affect goals, pathfinding, gathering, building, farming, exploration, role behavior, survival, social familiarity growth, remembrance rules, influence calculation, resource ownership, work groups, or movement.

There are no factions, politics, migration, settlement conflict, player controls, settlement bonuses, or same-settlement social bonuses in v1.

Future systems may use this identity layer for migration, splinter settlements, founders, settlement histories, multi-settlement worlds, ruins, and long-term lineage/history links.

## Social Bond Labels

Social bonds should describe familiarity before they imply family.

Social Bond Labels v1 are display-only labels derived from existing social memory. They do not create a relationship simulation.

Current labels:
- Familiar
- Friend
- Close Friend
- Trusted Companion

These labels are non-romantic and non-family. They must not imply partners, spouses, parents, children, siblings, couples, ancestry, reproduction, marriage, or pair bonding.

Family, reproduction, ancestry, children, romance, inheritance, and pair-bond systems are deferred until they are explicitly designed as lifecycle and generation systems. Household foundations now exist as village-unit membership, not family simulation.

Bond labels are shown compactly on villager character cards and are capped to the strongest few known villagers. They use existing familiarity levels rather than raw familiarity scores.

Social Bond Labels do not affect AI, movement, pathfinding, gathering, building, farming, state labels, death/remembrance behavior, influence calculation, settlement membership, survival, social-memory growth, or any other gameplay behavior.

In v0.6 these labels remain non-family and non-romantic. Household foundations, reproduction, ancestry, children, and parent-link systems should be designed explicitly through the lived-in settlement and generational roadmap rather than inferred from Social Bond Labels.

## Pre-Existing Social History

The v0.7 starting village seeds quiet prior life so villagers do not all begin as strangers.

Seeded startup data:
- years in role
- routine age
- workplace familiarity
- household familiarity
- personal memory snippets
- social-memory familiarity from shared household, workplace, and role history

Relationship strength is derived from shared history:
- household members gain familiarity based on household established years
- coworkers gain familiarity based on overlapping workplace routine
- villagers with the same role may know a few long-running peers

Starting memories are grounded in settlement activity, such as shared households, steady work routines, workplace history, and long-running role practice. They are not dramatic fabricated events.

Pre-existing social history remains observer-facing. It does not affect AI, pathfinding, work assignment, gathering, building, farming, survival, reproduction, inheritance, romance, family trees, or player controls.

## Household Foundations

Households are village-unit membership records used to make the starting settlement legible and to prepare for future generations.

Each household has:
- household ID
- household name
- home ID / home building ID
- member IDs
- founder IDs
- founded year
- household head
- cohabitation duration

Each villager has:
- household ID
- home ID
- parent IDs
- child IDs
- generation

Each home belongs to one household. Villagers belong to exactly one household, keep a stable home anchor, and return to that same home during night behavior.

Household cohabitation reinforces existing social memory once per day. This is a lightweight familiarity hook only: it does not assign work, choose partners, create children, alter survival, or replace the explicit relationship/generation systems planned later.

Selecting a house shows the household name, ID, members, founded year, head, and size. Settlement information can summarize household count, average household size, and largest household.

Households do not implement marriage, childbirth, inheritance, romance, family trees, dynasties, politics, or household controls. They are community context and future data architecture only.

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

## History Overlay

The History overlay is a read-only village chronicle.

Its purpose is to make the simulation readable as a story.

It is not a management tool.

It is not a debug console.

It is not a death viewer, graveyard UI, or memorial-management UI.

History Overlay v1 uses the existing Overlay Framework and opens with `H`. It reads existing world data rather than creating separate storage for UI.

Current Chronicle content includes:
- recent world-history entries
- active remembrance lines such as `Ari is remembering Rowan.`
- remembered dead from permanent Death Records

History entries should use readable player-facing language and season/year dates where possible, such as `Summer, Year 2`, instead of raw ticks or debug counters.

Remembered dead are shown as compact story cards with name, role, lifecycle stage, influence label, cause of death, date, and remembered-by names when available.

Future Chronicle content may include settlement founding, first farms, first workshops, shortages, influential villagers, visitors, mysteries, migrations, leaders, ruins, and legends. Those event types should slot into the same Chronicle structure later, but are not implemented in v1.

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

The sprite style is inspired by compact Game Boy Color-era RPG character presentation without copying specific sprites, characters, palettes, or assets. Villagers should read as cute chibi RPG people rather than blocky icons or voxel-style figures.

Sprite proportions should favor:
- a large head, roughly half the sprite height
- a compact body
- short legs
- a rounded silhouette

Hair is the primary visual differentiator. Hairstyles, hair shape, and hair silhouette should help villagers feel recognizable at a glance.

Sprites reflect appearance, lifecycle stage, and role color:
- appearance controls skin tone, hair color, hair style, face shape, and eye placement
- elders use grey / white hair
- clothing uses the same role colors used for villagers on the map
- clothing uses a simple highlight / midtone / shadow palette derived from the role color instead of a single flat fill
- simple pixel shading on hair and clothing gives the sprite charm and depth without becoming realistic

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

The lived-in settlement roadmap should eventually support renewal and expansion paths:
- Food pressure can lead to farming.
- Population pressure can lead to migration or a new settlement.
- Households and lifecycle systems can support births, deaths, aging, and inherited traits.
- A small group may later decide to leave, travel or abstractly depart, and found or record a new settlement.
- Migration should not require diplomacy, politics, warfare, or a full economy first.

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

## Survival Economy Balance v1

Survival work has priority over expansion when the village is under pressure.

Implemented behavior:
- critical hunger interrupts current work and seeks food if no carried or stored food is available
- critical thirst interrupts current work and seeks water if no carried or stored water is available
- food and water crises redirect routine labor away from construction and wood gathering
- simultaneous food and water crises split villagers between food and water work instead of sending the whole village to one resource
- food, water, and wood workers carry small batches before returning to storage
- food and water actions are intentionally shorter than wood chopping and construction

Design boundaries:
- this is a prioritization and throughput balance pass, not arbitrary resource generation
- local resource preferences remain soft, and urgent survival can still use any reachable known resource
- construction should resume once survival buffers recover
- long-running construction remains incremental so villagers can be interrupted between progress ticks

Current balance constants favor a small survival buffer: food targets roughly three days of population needs, and water targets roughly two days.

Settlement planner balance correction:
- wood demand exists only when reserves are below target or active construction needs wood
- builders without construction work support meaningful food or water shortages before gathering wood
- stable builders fall back to support rather than creating a permanent wood surplus
- resource rows show a simple status label such as Low, Stable, Stocked, Needed, or Surplus so storage targets read as health signals rather than raw pass/fail counters

## Seasonal Resource Ecology Foundations

Wild food is a seasonal natural resource, not an infinite pantry.

Implemented behavior:
- harvesting wild food removes available food from the tile
- a wild food node that is harvested to zero enters a short depleted cooldown before it can regrow
- Spring and Summer support strong new wild food growth
- Autumn growth is reduced
- Winter allows existing food to be harvested but does not create new wild food growth
- stored food is tracked in simple age batches and spoils after a fixed number of days
- spoiled stored food is removed from both abstract colony storage and visible food stockpiles
- the colony summary shows local wild food count and a seasonal food status such as Growing or Winter Dormant

Design boundaries:
- wild food and farm food remain separate concepts: wild food lives on terrain tiles, farm food lives on `FarmPlot`
- no planting, crop choice, preservation, farming profession, irrigation, or farm production-chain expansion is introduced here
- future farms can use different growth, harvest, and spoilage rules without changing wild food ecology

## Workplace Placeholders v1

Workplaces provide a shared data and visual foundation for future professions without adding new production chains.

Implemented behavior:
- settlements register workplace placeholders for storage, farm area, workshop, and village center
- each workplace has an id, type, position, capacity, footprint tiles, and assigned worker ids
- starting villagers may reference a workplace, but workplace assignment does not drive profession logic yet
- farm workplaces are visual placeholders and do not create productive farm plots at startup
- seeded village paths connect homes and core workplace areas

Design boundaries:
- no new farming, crafting, blacksmithing, crop growth, or profession output is introduced
- existing stockpiles, workshops, and future farms remain the production surfaces until profession systems are designed
- workplace data exists so future jobs can claim stable locations without inventing another registry

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
- farms use crop states: Unprepared, Planted, Growing, Ready For Harvest, and Dormant
- Spring is the planting season and consumes stored seed reserves
- Summer advances planted crops through growth
- Autumn turns crop growth into seasonal harvest batches
- Winter leaves empty fields dormant
- drought reduces farm growth and heavy rain improves it through the existing environmental event model
- ready farms can be harvested through farm work or urgent food behavior
- harvests produce stored seed reserves as well as food, and villagers cannot eat seed reserves
- the settlement planner can assign villagers to `farming` work when fields need planting or harvest
- farm workplaces track assigned workers and active field tiles as the basis for future farmer specialization
- Resource Reservation v1 can reserve a farm plot while a villager is moving to harvest it
- critical hunger can still override farm reservations when no alternative exists
- farm plots render as terrain-like interiors with a brown outline around the whole 2x2 plot and simple symbols for crop state

Design boundaries:
- no player farm placement
- no farming setup UI
- no crop selection, irrigation, soil simulation, preservation, or profession UI
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

## Right Panel Summary v2

The right panel is a player-facing observation dashboard.

Implemented behavior:
- world identity remains the top anchor
- Day, Year, Season, and Speed appear in a compact two-row grid below the identity
- the separate debug-style Simulation section is removed from the default summary
- Colony answers one question: how is the colony doing right now?
- Colony shows compact tier-one health signals: population, homes, households when available, food status, water status, and housing status
- planner priorities, resource targets, workforce allocation, farm counts, production statistics, and detailed reason text are reserved for future overlays
- detailed values such as settlement center, radius, claims, farm growth, farm food, workshop progress, and capacity estimate live in selected-object details

Design boundaries:
- no gameplay logic changes
- no model data removal
- no population current/max display
- no planner diagnostics in the default HUD
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
