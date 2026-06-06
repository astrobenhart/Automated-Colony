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

Goal: Make agents survive through memory, goals, and pathfinding.

Features:
- [/] Refactor into modules
- [ ] Add BFS pathfinding
- [ ] Add agent memory
- [ ] Add goal system
- [ ] Add selected-agent UI
- [ ] Add lightweight tests

## v0.3 - Smarter World

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
- Worlds no longer look uniformly random
- Rivers connect logically from high ground toward lower ground
- Forests appear more often near water or in wet regions
- Food and wood availability depend on biome
- Seasonal changes visibly affect resource growth
- Agents must adapt to world conditions rather than only random resource placement

## v0.4 - Colony Behavior

Goal: Make agents act more like a colony.

Features:
- [ ] Shared knowledge
- [ ] Roles
- [ ] Storage
- [ ] Farming
- [ ] Building priorities
- [ ] Migration or population replenishment

## v0.5 - Social Simulation

Goal: Add relationships and social structure.

Features:
- [ ] Families
- [ ] Friendships and rivalries
- [ ] Leadership
- [ ] Jobs
- [ ] Reputation
- [ ] Group decisions

## v0.6 - History and Emergence

Goal: Make the world generate stories over time.

Features:
- [ ] Named settlements
- [ ] Major historical events
- [ ] Timeline view
- [ ] Disasters
- [ ] Ruins
- [ ] Myths or legends
