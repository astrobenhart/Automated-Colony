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
- preserve selection, active events, history, contextual tile inspection, controls, and recent event visibility without changing simulation behavior
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
- Pioneer Camp: a 0-2 year frontier start with 12-20 villagers, fewer buildings, limited stores, and visible survival pressure.
- Growing Village: recommended v0.7 default, with 30-60 villagers, homes, farms, paths, workplaces, simple households, existing routines, and social bonds.
- Mature Settlement: a 20-50 year start with established infrastructure, stronger social memory, older paths, and deeper Chronicle context.
- Ancient Hamlet: a 50+ year start with old households, long Chronicle history, stronger traditions, and more unresolved folklore.
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
- In v0.7 these fields were static startup metadata; aging progression, children, births, and inheritance were left for v0.8 generational systems.

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

## Generational Architecture Foundation

v0.7 adds generation-ready data structures without enabling reproduction.

Villager lifecycle model:
- birth year and birth day
- current age
- lifecycle stage
- death year and death day
- alive/deceased status
- lifecycle history record for future age progression

Family structure model:
- mother ID
- father ID
- parent IDs
- child / children IDs
- sibling IDs
- partner IDs
- generation number

Household lineage model:
- founder IDs
- household head
- founding year
- generation count
- historical member IDs
- succession history

Inheritance architecture:
- personality traits
- work preferences
- social tendencies
- appearance traits

Memory and relationship extension:
- future relationship types include acquaintance, friend, household member, parent, child, sibling, and partner
- future family memory categories include parent, child, sibling, household elder, and family loss
- current social memory remains score-based and display-only

Chronicle support:
- future categories include births, family events, and household succession
- death records preserve household, home, generation, parent, child, sibling, birth year, and death year fields

Future v0.8 reproduction flow:
1. Advance ages on a scheduled cadence.
2. Move villagers through lifecycle stages.
3. Evaluate household-based reproduction eligibility.
4. Create a child with parent IDs, household ID, generation, inherited trait profile, and birth Chronicle entry.
5. Add household historical membership and family memories.
6. Apply renewal through probabilistic old-age mortality, household succession, and family Chronicle entries once births and adulthood are stable.

This architecture avoids pregnancy, childbirth complications, marriages, genetics, inheritance law, romance drama, and family-tree UI.

## v0.8 Partnership Foundation

Partnerships are the first v0.8 generational loop foundation.

They are:
- stable long-term pair bonds
- derived from existing social familiarity
- limited to one active partner per villager
- evaluated as an infrequent daily social pass
- recorded in villager memory and the Chronicle
- lightly integrated with households when doing so does not disrupt existing stable homes

They are not:
- marriage
- dating
- romance drama
- legal family structures
- attraction mechanics
- a reproduction or birth system

Eligibility stays deliberately narrow:
- living adult-stage villagers
- same settlement
- no current partner
- no direct parent, child, or sibling relationship
- sufficient existing familiarity from household, workplace, or routine history

Household integration is renewal-oriented. Partners already sharing a household stay there. If one partner lacks a household or lives alone, they may join the other partner's household. If both partners belong to established multi-person households, they form a new household record with no home yet; the existing residential planner then creates normal housing demand and builders construct the new home through the usual task pipeline. This keeps partnerships as social bonds, not marriage or romance simulation, while ensuring stable adult partnerships can become shared households across generations.

Future birth systems should use partnerships as one input into household-based renewal, not as a complete family simulation.

## v0.8 Partnership Lifecycle

The partnership lifecycle is:

Adult
-> Partnership
-> Household Formation
-> Household Growth
-> Household Expansion
-> Next Generation

Partnerships describe stable adult social relationships. Households describe the physical living arrangement. Births require both: an established partnership and a shared household.

When partners can safely share an existing household, one partner joins the other household. When both partners are already embedded in established households, they found a new household and become a residential demand for the normal construction system. The simulation should not rely on a lucky overcrowding side effect before partners can live together.

Death naturally ends an active partnership. The deceased villager remains in memories and history, but the surviving partner's active `partner_id` state is cleared so they can eventually participate in future partnership formation. This is lifecycle cleanup, not a breakup or romance mechanic.

## v0.8 Birth Foundation

Births are the second v0.8 generational loop foundation.

They follow the simple loop:
- partnership
- shared household
- birth
- child villager enters the world

Births require:
- both partners alive
- an established partnership
- shared household membership
- adult-stage parents
- same settlement membership
- available housing space
- basic food and water reserves

The birth pass runs daily with low probability and a cap on new children per day. It is resource-aware, but it is not a population-balancing system and does not create children to fill labor shortages.

Children are real villagers with parent IDs, household membership, generation number, inherited trait identity, memories, and Chronicle birth entries. They are dependents until lifecycle progression moves them into adult-stage village life.

The birth phase does not implement pregnancy, gestation timers, fertility simulation, childbirth risks, child jobs, inheritance law, family trees, or family reputation.

## v0.8 Lifecycle Progression

Lifecycle progression is the third v0.8 generational loop foundation.

It follows the simple loop:
- child villager exists in a household
- child consumes food, water, and housing capacity
- daily lifecycle pass updates age from birth date
- child reaches adulthood
- new adult becomes eligible for work and future partnerships

Children are members of their household and remain tied to the same home. They do not gather resources, build, farm, form partnerships, or receive profession-specific work while they are children. Their daily behavior remains lightweight: stay near home, satisfy emergency needs, and age normally.

The aging pass runs daily. Starting adults keep their seeded ages, while children born during simulation age from `birth_year` and `birth_day`. When a child reaches the adulthood threshold, the villager enters the adult-stage population as a Young Adult, preserves inherited traits and household membership, and becomes eligible for existing workforce assignment.

Lifecycle events are intentionally low-volume. A child reaching adulthood creates a personal memory, parent memories when parent links exist, and a Chronicle family entry for later-generation villagers. No education system, apprenticeship path, child profession, elder transition, old-age death, inheritance law, or family tree visualization is implemented in this phase.

## v0.8 Family Identity

Family identity is the fourth v0.8 generational loop foundation.

Families are persistent lineage and history entities. They are separate from households:
- households describe where villagers live
- families describe who villagers descend from

Every villager belongs to exactly one family. Starting villagers are assigned to founding family records during world creation. Children inherit family membership at birth, and moving households does not change family identity.

Family records track:
- unique family id and display name
- founders and founding year
- living and deceased members
- generation count
- parent family links for future genealogy
- low-volume family memories
- births by year for diagnostics and balancing

Biological relationship tracking remains lightweight. Children store parent ids, parents store child ids, and siblings are linked when children share a parent. These relationships are queryable when needed; the simulation does not rebuild expensive family trees every frame.

Trait inheritance remains simple and display-first. Births now create an inheritance profile from parent traits, roles, experience labels, and appearance metadata with small variation. The child's direct trait is still lightweight; no genetics, aptitude math, inherited professions, or inheritance law is introduced.

Family memories are permanent family-level records. They survive individual villager deaths and record milestone events such as first child, adulthood, and family loss. Major family milestones may also feed the Chronicle as narrative entries.

Diagnostics include number of families, average family size, largest family, oldest family, current generation depth, and births by family this year.

Design boundaries:
- no marriage system
- no surname simulator
- no family tree UI
- no family reputation
- no inheritance law
- no politics or legal family structures
- no per-frame genealogy computation

Future work can add genealogy viewers, ancestral homes, inherited professions, famous bloodlines, surnames, or dynasty display by reading the family registry rather than redesigning villager or household data.

## v0.8 Renewal

Renewal is the fifth v0.8 generational loop foundation.

The first complete loop is now:
- adults form stable partnerships
- partnered households may have children
- children age into working adults
- families persist across generations
- elders die naturally
- households choose successors
- the Chronicle remembers the passing of generations

Natural death is lifespan-based rather than fixed-age. Each villager receives an expected lifespan derived from deterministic village seed data and light identity variation. Mortality begins conservatively in old age, rises after the expected lifespan, and is modestly influenced by long-term wellbeing signals such as hunger, thirst, and fatigue pressure.

Deaths run in the daily renewal pass, not every tick. This keeps mortality aligned with Simulation LOD and prevents expensive or noisy per-frame checks.

Household succession preserves household identity after a head dies. The successor preference order is:
- surviving partner
- adult child
- oldest adult resident
- oldest resident as a fallback if no adult remains

Household succession appends compact succession history to the household and records a Chronicle entry. Household members and historical member records remain intact; the household does not vanish because a founder dies.

Family succession remains simpler: families continue as persistent lineage records. Founder deaths move members from living to deceased, add family memory, and may add a Chronicle entry when the family has surviving continuity.

Household division remains part of the Residential Growth Model. When an overcrowded max-size household has adult partnered residents and a new home is constructed, the partnered pair can establish a new household. The split is recorded as a renewal Chronicle event.

Birth balance now uses effective support rather than stored food alone. Birth eligibility considers stored food, ready farm food, bounded local food, stored water, and local water access. Births remain uncommon through low per-pair probability, dependent-child spacing, and a cap on dependent children per household.

Population renewal also applies a final birth-probability multiplier after a couple has passed every existing eligibility gate. The multiplier depends only on settlement population pressure, measured as current population divided by housing capacity. Lower pressure increases the final probability according to the configured renewal tiers, while high housing pressure returns the multiplier to 1.0x. This does not bypass housing, food, water, household, partnership, parent-age, child-spacing, or dependent-child requirements. It represents peaceful, well-supported villages naturally tending toward larger families.

Diagnostics expose:
- age distribution
- expected deaths this year
- natural deaths this year
- generation distribution
- household succession events
- household split events
- family generation depth
- births by family this year

Design boundaries:
- no inheritance law
- no wills or property transfer
- no elder wisdom mechanics yet
- no heirlooms
- no family professions
- no dynasty/reputation mechanics
- no family-tree UI
- no deterministic fixed-age death

Future inheritance, ancestral homes, elder wisdom, heirlooms, family professions, and dynasty presentation should build from household succession history, family records, and death records rather than changing the renewal loop.

## Residential Growth Model

Housing growth is household-driven.

The settlement no longer maintains artificial reserve beds for possible future births. Instead, residential demand emerges from actual household state:
- a household has no residence
- a household is overcrowded and can expand
- a partnered adult pair in an overcrowded max-size household can split into a new household

Each house tile provides physical household capacity. A household's capacity is the number of connected house tiles assigned to that household multiplied by the house-tile capacity constant. Households may temporarily exceed capacity; overcrowding creates pressure to expand or split rather than immediate failure.

House expansion rules:
- expansion must create a new house tile orthogonally adjacent to an existing house tile owned by the household
- diagonal expansion does not count
- each household has a maximum number of house tiles
- expansion uses normal construction work and resource costs

When a household reaches maximum physical size, partnered adult members may eventually found a new household. New households begin with a single house tile; future growth happens through the same expansion path.

Developer diagnostics on the settlement track:
- overcrowded households
- homeless households
- household split candidates
- house expansion candidates
- total house tiles
- total house capacity

Birth requirements remain strict and household-based. Births can create manageable overcrowding when a household has room to expand, which lets the village respond physically after family growth instead of pre-building spare capacity.

## Residential System Transition

The active residential model is now House.

A house represents:
- a household residence
- living space
- family space
- population capacity

Earlier versions used shelter as the survival-era residential concept. That distinction no longer maps cleanly to households, partnerships, births, parent links, Chronicle history, or future inheritance and succession.

New residential construction creates houses and registers them with the settlement home list. Housing capacity is calculated from houses, with legacy shelter tiles still counted for backwards compatibility until a future save migration can convert or retire them.

Planner and UI language should use housing, houses, and housing capacity. Legacy code names such as `BuildShelterAction`, `needed_shelters`, or `shelter_capacity` may remain temporarily as compatibility aliases, but they should be treated as migration debt rather than current design language.

## Settlement Diagnostics Window

The Diagnostics overlay is a development and balancing tool toggled with `D`.

It is read-only and intentionally separate from the compact right-hand colony panel. The panel remains player-facing and at-a-glance; diagnostics exposes internal state for debugging households, partnerships, births, housing, resources, workforce, mood pressure, and performance.

Diagnostics sections include:
- population and generations
- child, adult, and lifecycle transition counts
- household and housing pressure
- partnership eligibility and duration
- birth attempts, successes, eligible pairs, and current blockers
- resource storage, targets, and estimated flow
- workforce assignment counts
- derived mood pressure from needs and overcrowding
- simulation/render/pathfinding performance counters

The window should remain lightweight. Expensive historical analysis, family-tree rendering, inheritance reports, and detailed production ledgers should be added as explicit future diagnostics rather than folded into the right panel.

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

## Friendships

Friendships are memories created by shared life.

They are not jobs, commands, conversations, dialogue, quests, or a relationship graph. Villagers do not decide to run a `become friends` task. Instead, friendship grows when existing village life repeatedly places people together.

Purpose:
- make villagers feel like members of a community
- let the player recognise small social groups over time
- provide a foundation for romance, mourning, celebrations, wanderers, personality, and the Living Chronicle
- support memorable stories without creating a complex social simulator

Formation rules:
- household members strengthen friendship through daily cohabitation
- assigned coworkers strengthen friendship through shared workplace life
- nearby idle or routine presence can strengthen friendship slowly
- shared activity such as construction, harvesting, gathering, or other visible work can strengthen friendship
- repeated interaction matters more than one dramatic event

Memory model:
- each villager stores only a small capped set of meaningful friendships
- friendship entries store friend id, display name, score, first formed day, and last interaction day
- the active friendship list is capped to the strongest known friends
- close friendships may be recorded in the Chronicle once when they become meaningful
- stale friendships may weaken slowly after a very long period without interaction, but they do not disappear quickly
- deceased friends are removed from active friendship lists so living friendship summaries remain current

Gameplay effects:
- effects are intentionally subtle
- idle wandering may sometimes prefer a place near a close friend
- mood diagnostics can show a small positive effect when a close friend is nearby
- close friend death can create temporary remembrance and a small mourning signal
- survival needs always dominate friendship preferences
- friendships never override hunger, thirst, fatigue, pathfinding safety, work completion, household rules, births, deaths, or construction

Chronicle integration:
- close friendship formation can create sparse local-story entries such as `Rowan and Ella became close friends.`
- close friend death can create sparse mourning entries such as `Thomas mourned the loss of Iris.`
- friendship Chronicle entries should remain uncommon and should prioritise meaningful long-term bonds over frequent social noise

Diagnostics:
- developer diagnostics expose average friendships per villager, close friendship count, average strength, most connected villager, friendship formations, and friendship losses
- these diagnostics exist for balancing and story debugging, not player optimisation

Design boundaries:
- no global all-to-all relationship graph
- no per-frame friendship comparison
- no player-managed social scheduling
- no dialogue system
- no jealousy, rivalry, social politics, or romance drama in this phase
- no survival penalties for lacking friends
- social bond labels remain display-only familiarity labels; friendships are the first lightweight social layer with subtle story-facing effects

## Village Gatherings

Village Gatherings are social gravity, not choreography.

They are not events, schedules, parties, conversations, dialogue, or group AI. The simulation does not tell villagers that a gathering is happening. Instead, idle villagers independently prefer places that already feel socially attractive.

Purpose:
- make free-time village life feel communal
- create visible small groups without scripting them
- give future Shared Moments, Celebrations, Wanderers, children playing, and traditions a natural stage
- let friends, families, households, and visitors influence where people drift

Participation rules:
- only free villagers can participate
- urgent hunger, thirst, fatigue, survival, work, construction, farming, hauling, sleeping, and emergencies take priority
- gatherings never interrupt existing work or survival behaviour
- children use the same attraction model but favour home, household, family, and trusted nearby adults

Destination selection:
- no new Gathering Place entity exists
- villagers score existing village locations such as the village centre, homes, friends' homes, workplaces, farm/workplace edges, and known water sources
- future taverns, markets, shrines, visitor camps, or celebration sites should become attractive by exposing ordinary world positions rather than requiring a separate gathering system

Social attraction:
- destinations become more attractive when villagers are already nearby
- close friends, household members, and family members increase attraction
- distance reduces attraction
- the village centre remains a mild shared anchor
- a small random factor prevents the same perfect destination being chosen every time
- attraction diminishes after a comfortable group size so large villages naturally form multiple gatherings instead of one crowd

Emergent behaviours:
- friends gathering
- families gathering
- visiting households
- shared meals
- children playing nearby
- wanderers drawing attention

These behaviours should emerge from destination choice. They should not become separate gathering systems.

Inspection and diagnostics:
- villager inspection can show a compact derived social state such as Working, Resting, Gathering, Visiting Friend, or Idle
- diagnostics derive active gatherings, average gathering size, largest gathering, idle participants, and destination labels from current villager positions
- ordinary gatherings do not create Chronicle entries; the Chronicle records meaningful events that may happen at gatherings later

Future integration:
- Celebrations can temporarily make a location more attractive without redesigning movement
- Wanderers can attract villagers simply by existing at a place
- Shared Moments can trigger when villagers are already standing together
- traditions can arise from repeated gatherings at the same kinds of places

Design boundaries:
- no explicit gathering schedule
- no party mechanics
- no dialogue or conversation system
- no global social search each frame
- no persistent gathering records unless a future story system needs them
- systems should create behaviours; behaviours should not become separate systems

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

Starting Chronicle seed entries include:
- settlement foundation and early development
- household founding and oldest-household notes
- workplace and infrastructure establishment
- population milestones appropriate to starting population
- environmental hardship or abundance
- grounded local stories tied to existing villagers
- one uncommon unresolved mystery

History entries should use readable player-facing language and season/year dates where possible, such as `Summer, Year 2`, instead of raw ticks or debug counters.

Remembered dead are shown as compact story cards with name, role, lifecycle stage, influence label, cause of death, date, and remembered-by names when available.

Seeded Chronicle entries are stored in `WorldHistory` before normal simulation events are appended. The History overlay sorts all entries chronologically, so startup history and later events form one continuous record.

Mystery entries are atmospheric only. They have no explanation, no monsters, no combat, and no direct magical mechanics.

Future Chronicle content may include births, deaths, partnerships, household continuity, inheritance, magical events, major settlement developments, influential villagers, visitors, mysteries, migrations, leaders, ruins, and legends. Those event types should slot into the same Chronicle structure later.

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

## Living Forest Rendering

Forest rendering is visual only. A forest tile remains one simulation tile, one pathfinding tile, and one harvestable wood/food resource node.

Each visible forest tile is rendered as a deterministic microtile canopy. Microtile colours are derived from world seed, tile coordinates, render detail, and the tile's current visual season. No frame-randomness is used, so forests do not flicker.

Seasonal forest palettes:
- Spring: cohesive green shades with uncommon fresh growth accents
- Summer: dense dark/bright greens with rare trunk-brown subcells
- Autumn: green, yellow, orange, red, and muted brown transitions
- Winter: brown, dark brown, grey-brown, with occasional evergreen green

Forest appearance is stable within a season. When a new season begins, each forest tile receives a deterministic transition day within the first few days of that season based on world seed, tile coordinates, and season. Until its assigned day, the tile keeps the previous season's canopy. On its assigned day, it switches once to the new season palette.

The cached map surface is rebuilt only when the visible camera region, season transition state, environmental state, discovery counts, or structure counts change. Villager rendering remains dynamic and independent of the terrain cache.

Future biome presentation can reuse the same pattern for young forest, mature forest, ancient forest, harvested forest, burned forest, or magical forest states without adding new simulation behaviour.

## Living Water Rendering

Water rendering is visual only. A water tile remains one simulation tile, one unwalkable pathfinding tile, and one stable water source for villager behaviour.

Each visible water tile is rendered as a deterministic microtile surface. Microtile colours are derived from world seed, tile coordinates, render detail, and the tile's current visual weather state. No frame-randomness is used, so lakes, rivers, and ponds do not flicker.

Initial water weather palettes:
- Clear: deep blue, blue, and light blue with subtle variation
- Rain: lighter blues, muted reflection tones, and occasional grey-blue subcells
- Heavy Rain: brighter highlights, darker pockets, and cooler disturbed-water tones

Weather state is renderer-facing and derived from active environmental events. Heavy rain events render water as Heavy Rain. Future rain-like event types can render as Rain without changing tile semantics.

When water weather changes, each water tile receives a deterministic transition tick over a short in-game-hours window based on world seed, tile coordinates, weather state, and transition id. Until its assigned tick, it keeps the previous weather palette. On its assigned tick, it switches once to the new weather palette.

The cached map surface is rebuilt only when the visible camera region, seasonal transition state, water weather transition state, environmental state, discovery counts, or structure counts change. This keeps water responsive to weather without continuous animation or per-frame work.

Future environmental presentation can reuse the same pattern for storms, drought shoreline tinting, frozen water, flooding, or magical corruption without changing pathfinding or water availability.

## Living Grass Rendering

Grass rendering is visual only. A grass tile remains one simulation tile, one ordinary walkable terrain tile, and keeps the same pathfinding, building, resource, and save behaviour.

Each visible grass tile is rendered as a deterministic microtile surface. Microtile colours are derived from world seed, tile coordinates, render detail, season, base moisture from the generated moisture map, and the current visual moisture mode. No frame-randomness is used, so grass does not flicker.

Grass visual moisture states:
- Dry: yellow-green, brown-green, and dry patch tones
- Normal: medium seasonal greens
- Wet: deeper, richer greens or darker dormant tones

Seasonal grass palettes:
- Spring: rich greens, bright new growth, and healthy vegetation
- Summer: medium greens, faded tones, and occasional dry highlights
- Autumn: muted greens, yellow-green, and brown-green
- Winter: brown, muted green, and dormant vegetation

Environmental events modify visual moisture without changing gameplay. Heavy rain and future rain-like events push grass toward Wet. Drought pushes grass toward Dry. Clear weather returns grass to its base moisture state from the world moisture map.

When visual moisture mode changes, each grass tile receives a deterministic transition tick over a short in-game-hours window based on world seed, tile coordinates, moisture mode, and transition id. Until its assigned tick, it keeps the previous moisture palette. On its assigned tick, it switches once to the new palette.

Future terrain presentation can reuse this pattern for irrigation, snow cover, burnt terrain, overgrazed grass, marsh expansion, magical corruption, or farmland visual progression without changing movement or resource rules.

## Terrain Rendering Framework

Terrain rendering is presentation-only. Terrain tile kinds, pathfinding, resource rules, saves, and simulation behaviour remain owned by world and tile systems.

All visible terrain tiles now render through the shared `TerrainRenderer` pipeline:
- Build a renderer-facing visual state from world state, tile kind, season, weather, moisture, and environmental events.
- Build a renderer-only neighbourhood snapshot from the eight adjacent terrain tiles.
- Select colours through the centralized `TerrainPaletteManager`.
- Generate a deterministic microtile pattern through `TerrainPatternGenerator`.
- Apply deterministic edge masks so neighbouring terrain can soften tile boundaries.
- Draw the tile while preserving gameplay overlays such as farms, resources, homes, workplaces, villagers, and wildlife.

The visual state layer separates simulation state from appearance. A forest tile remains `forest`, a water tile remains `water`, and a path tile remains path-like even when their rendered palettes change. Renderer-facing fields such as visual season, visual weather, and visual moisture are presentation inputs only.

Every terrain tile uses the same adaptive microtile visual language. Specialized terrain palettes remain available for grass, forest, and water, while other terrain types derive subtle palette variation from their seasonal/environmental base colour. This keeps existing terrain recognizable while removing the old split between custom microtile terrain and single-colour terrain.

Pattern generation is deterministic. The renderer uses world seed, tile coordinates, terrain type, and visual state identity; it does not use frame-based randomness. Cached map rebuilding remains driven by existing cache keys for camera region, seasonal transition state, weather/moisture transition state, environmental state, discovery counts, and structure counts.

Future environmental presentation should extend the palette and visual state layers rather than adding new one-off draw paths. Planned extensions include snow cover, drought stress, burnt terrain, magical corruption, frozen water, flooding, crop growth stages, ancient forests, biome-specific palettes, and terrain wear variations.

### Renderer Configuration

Renderer art direction is loaded from `data/rendering/default.json` through `src/renderer_config.py`. The configuration is loaded once and normalized into immutable tuples for fast renderer use. This separates simulation, renderer logic, and art assets:

```
Simulation state
  -> TerrainRenderer
  -> Renderer art config
  -> Final microtile output
```

The current config owns:
- Master seasonal vegetation palettes.
- Vegetation harmony strengths.
- Terrain palette adjustment factors.
- Terrain motif lists.
- Path wear palettes.
- Ambient occlusion strengths and mask chances.
- Path visual language flags and forest encroachment tuning.
- Reserved sprite pipeline layers for future assets.

This is not live-reloaded yet, but the loader is centralized so future live tuning can clear and refresh the config cache without rewriting terrain systems. Future sprite assets should use the same config family for seasonal tinting, environmental tinting, sprite layer ordering, offsets, and theme selection.

Renderer style rules:
- Natural terrain should feel irregular, clustered, organic, and softly varied.
- Constructed terrain should feel deliberate, geometric, ordered, and readable.
- Paths are constructed terrain. Their normal rendering keeps crisp route identity instead of using organic edge shaping.
- Nature may subtly reclaim constructed terrain only through explicit effects, such as forest-adjacent path encroachment.

### Neighbour-Aware Edge Shaping

The simulation remains a square grid. The renderer hides some of that grid by letting each terrain tile inspect the eight surrounding terrain kinds:

```
NW N NE
 W X E
SW S SE
```

This neighbourhood is copied into `TerrainRenderContext` during rendering. It is read-only, is not saved, and does not affect movement, resources, pathfinding, AI, ownership, terrain kind, or construction.

`TerrainEdgeShaper` applies deterministic edge ownership masks after the base microtile pattern is generated. Edge masks operate on the selected microtile resolution, so the same logic works for LOW, MEDIUM, HIGH, and ULTRA detail. The masks may assign an outer-ring edge or corner microtile to either the owning tile terrain or a neighbouring terrain, but they do not mix terrain palettes together. No alpha blending, transparency, cross-terrain colour interpolation, frame-randomness, or simulation state mutation is used.

Terrain identity is preserved by design:
- The centre microtile remains representative of the owning terrain.
- Neighbour influence is limited to the outermost microtile ring.
- Every microtile is drawn from exactly one terrain's palette.
- Edge masks shape silhouettes rather than melting terrain types together.

Terrain transition priority gives boundaries consistent visual behavior:
- Water can own shoreline edge microtiles while remaining visually crisp.
- Paths and worn ground keep readable route identity while gaining less rigid shoulders.
- Forests can create irregular canopy outlines without dissolving into grassland.
- Hills, plains, and grass can exchange occasional edge ownership while retaining their own palette identity.

Path rendering no longer uses natural edge shaping by default. Roads are part of the constructed visual language: straight sections remain crisp, corners remain readable, and intersections should communicate deliberate human construction. The path-border helper remains available for tests and future debug views, but ordinary roads should read as ordered worn terrain rather than bordered squares.

Forest-adjacent paths can receive subtle deterministic encroachment from the seasonal vegetation palette. This is a separate renderer effect, not generic edge shaping, and should never obscure road readability.

Future edge-aware terrain can reuse the same ownership system for snowlines, beaches, wetlands, crop field edges, frozen rivers, burnt terrain, cliffs, magical corruption, and biome transitions.

### Ambient Terrain Occlusion

Ambient terrain occlusion is a renderer-only depth effect. It is not a lighting engine, does not use directional shadows, and does not change terrain, movement, resources, pathfinding, AI, construction, saves, or simulation state.

The first supported contributor is forest canopy. Forest tiles do not darken themselves and do not gain a visible outline. Instead, eligible neighbouring ground can receive a very subtle deterministic shade where it sits under implied canopy overhang. The shadow belongs to the receiving terrain, not to the forest.

Current receiving terrain is intentionally narrow:
- Grass, plains, dry grass, and sparse wetland-like vegetation may receive canopy shade.
- Water, paths, farms, buildings, construction, workshops, stockpiles, mountains, hills, and forest tiles do not receive this effect.

The effect is constrained to preserve readability:
- Normal canopy influence reaches at most one microtile from a forest edge.
- At ULTRA detail, dense continuous forest can influence a second microtile with rapid falloff.
- The centre of the receiving tile remains unchanged.
- Colours are only darkened versions of the receiver's own colours, never black, grey, transparent, or forest-coloured overlays.

Masks are deterministic and use world seed, tile coordinates, neighbouring forest density, microtile position, and render detail. The result should feel like canopy height and volume rather than a visible forest border.

### Visual Cohesion Pass

Terrain rendering uses a shared seasonal vegetation palette from the renderer config to keep grass, plains, hills, forests, crops, and future vegetation within the same ecosystem. Terrain-specific palettes still exist, but the shared `TerrainPaletteManager` harmonizes them toward a master seasonal palette:
- Spring: fresh cohesive greens with restrained bright accents.
- Summer: mature greens and slightly dry meadow tones.
- Autumn: intentionally broader yellow, orange, red, and brown-green variation.
- Winter: muted dormant greens, browns, and grey-browns.

Spring and Summer palette contrast is deliberately reduced so large terrain regions read as continuous meadows and canopy masses. Autumn keeps stronger colour diversity as the visually expressive season. Winter remains restrained and quiet.

`TerrainPatternGenerator` now selects deterministic terrain motifs before placing microtile colours. Motifs replace independent per-microtile colour rolls with clustered, low-frequency structure:
- Forest: dense canopy, canopy mass, small clearing, shrub patch.
- Grass and plains: dense tuft, sparse tuft, meadow, flowering patch, worn patch.
- Water: calm surface, ripple cluster, muted reflection, rain disturbance.
- Paths: compacted earth, wheel rut, worn shoulder, packed track.

Motifs are selected from world seed, tile coordinates, terrain, visual state, and render detail. Adjacent microtiles often share a cluster colour, while small accents remain rare outside Autumn or specific motifs. This keeps interiors of forests, lakes, grasslands, and plains visually calmer, leaving most complexity to edges and gameplay overlays.

Edge shaping is intentionally crisp during the cohesion pass. Edge masks still create organic forest borders, water banks, path shoulders, and grassland transitions, but they use deterministic terrain ownership instead of blending terrain colours. This avoids muddy borders while preserving the renderer-only neighbourhood system.

Farms and crop visuals are harmonized with the same seasonal vegetation palette. Crop state remains gameplay-owned; only the final crop palette is adjusted so fields sit naturally inside the surrounding landscape.

Spring forests deliberately retain a darker, richer identity than grasslands. They share the Spring colour family but use reduced harmony strength so woodland still reads as woodland.

### Adaptive Microtile Detail

The simulation owns terrain tiles. The renderer owns visual detail.

Terrain rendering no longer assumes a fixed microtile resolution. `TerrainRenderer` requests a render detail level, and `MicrotileGrid` maps that level to a square visual grid:
- LOW: 1x1
- MEDIUM: 2x2
- HIGH: 3x3
- ULTRA: 5x5

The project default is HIGH, so each simulation tile currently renders as a 3x3 microtile pattern. This is a visual quality setting only. A terrain tile remains one simulation tile for movement, resources, saves, pathfinding, farming, construction, and inspection.

Palette selection is independent of detail level. `TerrainPaletteManager` chooses colours from terrain and visual state. `TerrainPatternGenerator` places those colours into as many microtiles as the selected detail level requires. Changing detail level must not require new palettes or gameplay data.

Future camera work can choose detail level based on zoom, viewport density, map size, or performance budget. That logic should call the renderer's detail-level API and should not touch world generation, pathfinding, AI, or terrain rules.

### Cached Terrain Pipeline

Terrain rendering now separates base surface invalidation from environmental visual transitions. The current renderer still uses one viewport-sized map surface, but it treats that surface as cached terrain rather than a frame-by-frame procedural render target.

Renderer invalidation is split into revision families:
- Terrain: broad viewport/detail/world surface changes.
- Season: season labels, distributed forest transitions, and final-day seasonal colour interpolation.
- Weather: renderer-facing water state transitions.
- Moisture: renderer-facing grass/path moisture transitions.
- Construction: construction and farm visual state changes.
- Overlays: resource, structure, workplace, and other map-symbol visibility changes.

Base cache changes still rebuild the viewport surface. Weather, moisture, season, and environmental transition changes use per-tile visual signatures instead. Each signature combines the tile's renderer-facing `TerrainVisualState`, neighbour signature, and lightweight overlay state. During a transition tick, the renderer scans the visible tiles and redraws only tiles whose signature has actually changed.

The terrain renderer also caches deterministic intermediate results:
- Palette and neighbour-palette lookups.
- Palette weight lookups.
- Motif pattern generation.
- Edge mask selection from neighbour signatures.
- Final microtile patterns by tile, visual state, neighbour state, render detail, and environment key.

This preserves the visual output while avoiding repeated full-surface regeneration during weather and moisture transitions. Future rendering should reuse the same visual signatures and revision families rather than introducing separate invalidation logic.

### Chunk Terrain Cache

The viewport terrain surface has been replaced by independent cached terrain chunks. Each chunk currently covers `16x16` simulation tiles and owns:
- A fixed-size Pygame surface.
- Dirty/full-dirty status.
- A set of dirty tiles for partial chunk updates.
- A cache state and visual revision counter.
- Last rebuild/redraw counts for profiling.

Frame rendering now determines visible chunks, rebuilds only dirty chunks, clips drawing to the map viewport, and blits cached chunk surfaces. Camera movement no longer invalidates terrain. If the camera moves within already cached chunks, frame rendering performs only surface blits. If the camera crosses into uncached territory, only the newly visible chunk row or column is built.

Dirty tracking works at two levels:
- Full-dirty chunks rebuild their full `16x16` surface. This is used for first builds, detail changes, and broad renderer invalidation.
- Tile-dirty chunks redraw only the changed tiles on the existing chunk surface. This is used by weather, moisture, season, and overlay signature changes.

The renderer exposes dirty helpers for future simulation hooks:
- `mark_tile_dirty(x, y)` for isolated visual updates.
- `mark_tile_and_neighbours_dirty(x, y)` for terrain edits that can affect edge shaping, ambient occlusion, or neighbouring silhouettes.

Weather and seasonal transitions still scan visible tile signatures to discover which tiles changed, then dirty only the affected chunks/tiles. Future simulation systems should eventually emit explicit dirty tile events for harvesting, construction, path wear, farm changes, fire, snow, flooding, and magic so the renderer does not need to infer those changes from cache-key scans.

The architecture is now:

```
Simulation
  -> Terrain visual state
  -> Dirty chunk queue
  -> Chunk surface cache
  -> Frame compositor
  -> Dynamic agents, selection, overlays, and UI
```

This is still synchronous, but the rebuild boundary is now chunk-local and ready for future background building, zoom-aware chunk variants, sprite layers, biome layers, and lighting layers.

### Layered Scene Compositor

The renderer is now organized as a scene compositor rather than a single terrain renderer. The initial frame pipeline is:

```
Terrain Layer
Vegetation Layer
Structures Layer
Agent Layer
Effects Layer
UI Layer
```

Layer responsibilities:
- Terrain Layer owns cached terrain chunks, terrain palettes, motifs, adaptive microtiles, environmental state, path rendering, edge shaping, and ambient terrain occlusion.
- Vegetation Layer is reserved for future vegetation sprites such as trees, shrubs, flowers, crop detail, and grass accents. Forest canopy detail remains baked into terrain chunks until sprite assets exist.
- Structures Layer represents human-built and static map objects such as houses, farms, workshops, stockpiles, workplace markers, and resource symbols. In this phase these are still composed into the terrain chunk surface to preserve existing visuals and cache behaviour, but the chunk rebuild path now calls structure-layer methods separately from terrain drawing.
- Agent Layer renders dynamic villagers and future mobile entities independently from cached terrain.
- Effects Layer is reserved for future transient visuals such as rain, snow, smoke, fire, particles, and magical effects.
- UI Layer owns selection highlights, right-panel information, diagnostics/history/villager overlays, cursor-level UI, and `pygame_gui` drawing.

The main frame renderer calls `compose_scene()`, which renders layers in order. UI and agent drawing never invalidates terrain chunks. Static chunk contents are still cached together for now, but the architecture now has explicit ownership boundaries for splitting vegetation and structure surfaces into their own chunk caches later.

Current render flow:

```
World state
  -> Renderer revision state
  -> Dirty chunk/tile tracking
  -> Terrain chunk cache updates
  -> Layer compositor
  -> Display
```

Future renderer events should target layers directly. Examples: tree harvested -> Vegetation/Terrain dirty, construction completed -> Structures dirty, villager moved -> Agent layer redraw, weather particle event -> Effects layer update. This keeps simulation behaviour independent from renderer implementation while allowing each layer to become independently cacheable.

### Environmental Reactivity

The shared terrain renderer consumes existing world state and does not create new simulation rules. Environmental rendering inputs are:
- Season and distributed seasonal transition timing.
- Weather events through renderer-facing moisture and water states.
- Moisture map values generated by worldgen.
- Existing path wear terrain kinds created by foot traffic thresholds.

Terrain-to-environment mapping:
- Forest: season only. Forests keep deterministic microtile canopy rendering and transition gradually during the first few days of a new season. There is no daily canopy drift.
- Water: weather only. Clear, Rain, and Heavy Rain choose weather-specific water palettes and transition over short in-game-hour windows.
- Grass, plains, and hills: season plus moisture. These terrain types share grassland moisture logic while retaining distinct palette adjustments for readability.
- Trampled grass, worn grass, dirt path, and established path: wear stage plus moisture. Existing traffic thresholds choose the terrain kind; the renderer darkens paths under wet conditions and uses lighter dusty earth tones under dry conditions.
- Other terrain: seasonal/environmental base colour with subtle microtile variation.

Transitions remain deterministic and distributed. Seasonal grassland and forest transitions use world seed, tile coordinates, season, and day of season. Weather and moisture transitions use world seed, tile coordinates, transition id, and current tick. No visual state relies on frame-randomness.

Path rendering intentionally uses existing wear stages rather than raw foot traffic counts. This keeps the map cache stable during ordinary movement while still making frequently travelled routes clearer as they cross trampled, worn, dirt, and established path thresholds.

### Gameplay-Driven Rendering

The terrain renderer answers what a tile currently looks like. Gameplay systems expose state; they do not own renderer branching.

The final palette is composed through a modifier stack:
- Base terrain
- Season
- Weather
- Moisture
- Gameplay state
- Special modifiers
- Deterministic microtile pattern
- Render

Current gameplay visual inputs:
- Farm plots expose crop state, growth, food, and fertility. The renderer maps current farm states into visual stages: Empty, Planted, Sprouting, Growing, Mature, Harvested, and Fallow. Existing farm symbols and borders remain as lightweight readability overlays.
- Construction sites expose existing settlement construction progress. The renderer maps progress into Foundation, Under Construction, and Completed visual stages. Construction mechanics and costs are unchanged.
- Path wear continues to use existing trampled, worn, dirt, and established path terrain kinds.

Future renderer-ready gameplay inputs are represented as optional visual modifiers rather than new terrain types:
- Forest lifecycle: Young Forest, Mature Forest, Ancient Forest, Harvested Forest, Recovering Forest, Dead Forest, Burned Forest.
- Construction/building state: Foundation, Under Construction, Completed, Expanded, Damaged, Ruined.
- Fire: Burning, Charred, Ash, Regrowth.
- Snow: Light Snow, Medium Snow, Deep Snow, Melting Snow.
- Flooding: Water Expansion, Wet Shoreline, Floodplain, Mud.
- Magic: Blessed, Corrupted, Enchanted, Cursed, Mystical.
- Biome presentation: Temperate, Boreal, Grassland, Wetland, Highland, Ancient Forest.

These are renderer states only. They do not create fire, snow, flooding, magic, crop mechanics, biome generation, damage, pathfinding changes, or resource changes. Future gameplay systems should attach or expose visual state and let `TerrainModifierStack` compose the final appearance.

## Contextual Tile Inspector

The right-hand panel no longer includes a permanent terrain legend. Terrain is expected to be readable from the rendered map itself: adaptive microtile terrain patterns, seasonal palettes, weather-reactive water, moisture-reactive grasslands, path wear, and farm/construction visual states carry the visual meaning.

The reclaimed panel space is used for a contextual Tile section:
- If a tile is selected, the inspector shows that tile.
- If no tile is selected and the mouse is over the map, the inspector shows the hovered tile.
- If neither is available, the inspector shows a compact empty prompt.

The Tile Inspector is data-driven. It combines base tile facts with renderer-facing visual state and gameplay state:
- terrain label
- visual season
- moisture state
- water weather state
- path wear and foot traffic
- discovered food and wood values
- walkability
- farms, crop state, crop stage, growth, yield, and fertility
- homes and household details
- stockpiles, workplaces, and workshops
- construction visual stage
- future visual modifiers such as snow, fire, flood, magic, damage, biome, or forest lifecycle state

The inspector is read-only and does not affect simulation, pathfinding, resource discovery, or renderer state. Future systems should contribute rows by exposing gameplay or visual state rather than expanding the right panel with new permanent diagnostics.

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

## Starting Scenario Maturity

Starting scenarios change initial conditions, not simulation rules. Every settlement still uses the same planner, households, workplaces, paths, relationships, chronicle, ecology, and villager task systems after generation.

Implemented scenario levels:
- Pioneer Camp: 0-2 years old, 12-20 villagers, 4-7 homes, limited reserves, sparse path wear, shorter chronicle, and lighter social bonds.
- Growing Village: 5-15 years old and the default v0.7 experience, preserving the 30-60 villager start and 8-15 home cluster.
- Mature Settlement: 20-50 years old, larger housing footprint, stronger workplace and household familiarity, more chronicle entries, and more worn village routes.
- Ancient Hamlet: 50-90 years old, older demographics, long-established households, strong social bonds, denser local stories, and several unresolved folklore entries.

Scenario scaling affects:
- population and home counts
- settlement age and household founding years
- age distribution and experience flavor
- initial reserves for non-default starts
- pre-seeded path wear
- relationship strength derived from shared history
- chronicle density, including environmental history, local stories, and mystery entries

Design boundaries:
- no separate rulesets per scenario
- no scripted success or failure states
- no reproduction, inheritance, children, family trees, or generational turnover yet
- mysterious events remain unresolved history and do not add magic mechanics
- Growing Village remains the stable default for current v0.7 balance and tests

## Simulation Level of Detail

Simulation LOD keeps the village visually lively while moving slow-changing systems away from the hot loop.

Implemented tiers:
- LOD 0 Visual Systems: movement interpolation, animation state, renderer feedback. Runs every render frame or tick.
- LOD 1 Active Task Execution: walking, hauling, harvesting, building, eating, sleeping, and workplace actions. Runs every simulation tick for the active rotating villager batch.
- LOD 2 Needs Systems: hunger, thirst, fatigue, and wildlife updates. Runs hourly with elapsed-tick scaling so per-day balance stays stable.
- LOD 3 Social Systems: relationship growth, household familiarity, workplace familiarity, and influence peaks. Runs daily.
- LOD 4 Settlement Planning: resource targets, workforce balancing, housing demand, workplace demand, farms, ecology, storage spoilage, and path decay. Runs daily or event-driven.
- LOD 5 Historical Systems: chronicle entries, remembrance expiry, demographic records, family history, and future summaries. Runs event-driven or as daily cleanup.

Developer instrumentation:
- `World.lod_stats` stores calls, last duration, total duration, and average duration per LOD tier.
- `World.lod_report()` returns rows sorted by total cost.
- Renderer frames record LOD 0 timing without adding player-facing HUD clutter.

Future generational cadence:
- Aging: daily or seasonal, not per tick.
- Birth eligibility: daily or seasonal household pass.
- Child creation: event-driven.
- Death checks for age/illness/accidents: daily or event-driven.
- Trait inheritance: only when a child is created.
- Family tree updates: event-driven on birth, death, household split, partnership, or adoption.
- Chronicle birth/death/family entries: event-driven.
- Demographic reports: daily, seasonal, or overlay-requested only.

Design boundaries:
- do not attach slow systems to movement or rendering loops
- do not recompute settlement-wide social, family, or planner state per tick
- keep active visible work responsive even as background systems slow down
- prefer event-driven updates whenever a future system changes rarely

## Headless Simulation Runner

Long-running validation must measure the actual game, not a calendar shortcut.

`SimulationRunner` is the canonical execution path for release validation, balance testing, regression probes, and performance benchmarking. It advances the world by calling `World.update()` for every simulation tick. It does not call `World.advance_day()` directly, because direct day advancement bypasses villager AI, movement, task execution, construction progress, residential completion, and household splitting.

Runner modes:
- Interactive: renderer enabled, UI enabled, frame limiting enabled, human-facing presentation active.
- Headless: renderer disabled, UI disabled, frame limiting removed, every gameplay tick still executed.
- Validation: headless execution with metrics, callbacks, seed batching, and report generation.

All modes must execute identical gameplay logic. Acceleration is allowed only by removing presentation overhead: rendering, UI, sleeps, frame limiting, and noisy debug display. It must not skip ticks, batch multiple gameplay updates into one, bypass AI, skip construction, skip planner work, or bypass household, birth, death, Chronicle, or resource systems.

The validation runner records wall-clock runtime, ticks executed, simulated days and years per second, estimated speedup over interactive play, peak memory when available, and domain metrics such as population, births, natural deaths, household splits, residential construction, resources, housing capacity, and Chronicle activity.

Design boundaries:
- use `SimulationRunner` or an equivalent `World.update()` loop for release validation
- keep `World.advance_day()` for targeted calendar tests only
- do not use daily fast-forward results as proof that construction-driven or task-driven systems are stable
- future validation infrastructure should add metrics around this runner rather than inventing new shortcuts

## Design Priorities

1. Emergence over scripting
2. Simulation over graphics
3. Readability over realism
4. Small systems that interact
5. Observable behavior
