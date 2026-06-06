# Changelog

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
