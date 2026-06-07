# Changelog

## v0.4.0 - Smarter World

### Added
- Rule-based world generation using elevation, moisture, and temperature maps.
- Larger explorable maps with camera panning and a larger default viewport.
- Rivers that trace downhill and integrate with existing water/pathfinding behavior.
- Natural terrain variety including hills, plains, wetlands, dry areas, forests, mountains, grass, water, and shelters.
- Seasonal cycle with Spring, Summer, Autumn, and Winter.
- Smooth seasonal terrain color transitions and season-aware terrain legend colors.
- Terrain and season based resource ecology with growth caps and gradual die-off.
- Environmental Event v1 with drought and heavy rain.
- Persistent world history for major environmental events.
- Ambient biome-based wildlife: rabbits, deer, boar, and waterfowl.
- Centralized world-generation settings and presets for normal, wet, dry, forest, and harsh worlds.
- Generated world identity with title, subtitle, survival outlook, and hidden future-facing tags.
- Terrain and wildlife symbol legend in the right panel.
- Compact side-by-side Simulation and Colony panel layout.
- Automated tests covering worldgen, seasons, ecology, events, wildlife, history, settings, identity, renderer behavior, and v0.4 adaptation evidence.

### Changed
- The player-facing worldgen experience is now discovery through generated world identity rather than menus or setup controls.
- Resource availability now depends on terrain, season, ecology, environmental events, and world-generation settings.
- The right-side panel shows world identity, active events, history, legend, controls, and recent events more compactly.
- Default viewport increased while keeping tile size unchanged.
- Agents now operate in worlds whose terrain/resources vary meaningfully by preset and seed.

### Fixed
- Terrain legend colors now match season-aware map colors.
- Seasonal visual changes blend before season boundaries instead of snapping abruptly.
- Resource growth no longer accumulates without terrain-based caps.
- Environmental events remain temporary, visible, and non-destructive to permanent water.
- v0.4 verification confirms agents respond to world conditions through goals, memory, shared memory, pathfinding, storage, shelter construction, and resource seeking.

### Known Follow-Ups
- Tune survival outlook labels so generated identities better predict actual short-run colony outcomes.
- Tune wet-world balance; one verification seed showed a favorable wet identity but a harsh survival result.
- Wildfire, flood, broader world history, settlement history, and village systems remain future work.

## v0.3.0 - Colony Foundation

### Added
- Shared colony memory for known food, water, wood, and shelter locations.
- Personal-first, colony-second resource seeking.
- Simple colony storage for shared food and wood.
- Storage actions and goals for depositing surplus and eating stored food.
- Building priority abstraction for shelter construction needs.
- Occupied-aware pathfinding and stuck recovery for blocked movement.
- Selected-agent and selected-tile inspection UI.
- Right-side panel sections for simulation status, controls, colony summary, selection details, and recent events.
- Automated tests for building priorities, storage, memory sharing, movement recovery, pathfinding, goals, world logic, and renderer selection helpers.

### Changed
- Villagers now use goal-based behavior instead of purely reactive action selection.
- Shelter construction is bounded by shelter capacity.
- Wood gathering for construction is tied to actual building priority.
- Thirst pacing is less punishing while remaining a survival threat.
- The current run command is now `python -m src.main`.
- README and roadmap now describe the modular v0.3 simulation instead of the v0.1 prototype.

### Fixed
- Agents no longer rely only on static-terrain pathfinding when moving around other agents.
- Blocked movement paths are cleared and retargeted after repeated stuck ticks.
- Shared memory is both written and consumed by agents.
- Long panel text and event log entries are truncated safely.

## v0.1.0 - Prototype

### Added
- Single-file Pygame prototype with random terrain, villagers, needs, resource gathering, shelter building, and event log.
