# Presentation Layer Audit

## Executive Summary

The Presentation Engine exists, but the game still feels tick-based because most of the renderer still consumes simulation state directly.

The strongest current improvement is villager position interpolation. That proves the architectural direction is correct. However, it is a narrow slice:

```text
World / Agent state
  -> PresentationEngine
  -> PresentationSnapshot
  -> Agent renderer
```

Most other visual systems still follow the older path:

```text
World / Tile / Tick state
  -> Renderer logic
  -> Pixels
```

The result is that movement is smoother, but the world still exposes simulation machinery through tile-snapped camera motion, tick-driven weather, tick-driven mystery lights, tile-based foliage overlays, static symbols, abrupt selection and UI updates, and renderer systems that repeatedly query gameplay objects.

The highest-impact next step is not prettier art. It is widening the Presentation Engine so it owns more of the visible world: camera, agents, environmental effects, foliage, water, selection, and time-based visual states.

## Current Architecture

Current simulation timing:

```text
main loop dt
  -> accumulator
  -> World.update() zero or more times per frame
  -> renderer.update_ui(dt)
  -> renderer.draw(...)
```

Current renderer composition:

```text
Terrain Layer
Vegetation Layer
Structure Layer
Environmental Overlay Layer
Agent Layer
Effects Layer
UI Layer
```

Current Presentation Engine:

- Observes living agents.
- Maintains `PresentationAgent` objects.
- Interpolates agent render positions.
- Produces immutable `PresentationSnapshot` objects.
- Feeds the agent layer.
- Does not run during headless simulation.

Current direct renderer dependencies:

- Terrain, vegetation, structures, weather, clouds, mysteries, selection, side panel, diagnostics, and history overlays still query `world`, `tile`, `settlement`, `history`, `active_environment_events`, `active_mysteries`, and `world.tick` directly.
- Camera state is integer tile based.
- Mouse picking and selection are tile based.
- Environmental animation mostly uses simulation ticks rather than presentation time.
- UI overlays refresh from world state on fixed timers.

## Strengths

- The simulation remains authoritative.
- Headless simulation does not require presentation.
- Agent interpolation has moved out of `Agent`.
- Renderer agent drawing now consumes presentation snapshots instead of gameplay agents.
- Terrain chunks are cached and mostly protected from atmospheric effects.
- The renderer already has conceptual layers, which gives the Presentation Engine natural expansion points.
- The design documentation now clearly states the intended Simulation -> Presentation -> Renderer boundary.

## Remaining Tick-Based Behaviour

The world still feels mechanical because many visual systems update only when simulation state changes or use simulation tick counters as animation clocks. Interpolation exists, but it is not yet the dominant presentation model.

Visible tick leaks include:

- Agents only move when simulation tile positions change.
- Agent facing snaps to direction vectors.
- Agents render as static symbols with no animation state.
- Idle villagers become perfectly still.
- Camera moves in integer tile steps.
- Selection highlights snap to simulation tiles.
- Weather particles use `world.tick`.
- Cloud shadows use `world.tick`.
- Strange lights use `world.tick`.
- Foliage overlay uses tile positions and tick-modulated highlights.
- Water has renderer states, but no continuous presentation object.
- Structures, farms, stockpiles, homes, and workshops render as static tile symbols.
- UI and history overlays rebuild from gameplay state rather than presentation-facing view models.
- Most renderer layers still query `World` directly.

## Ranked Findings

### Critical - Presentation Engine Is Agent-Only

Current Architecture:
The Presentation Engine owns only agent presentation. Terrain, vegetation, weather, clouds, mysteries, water, structures, selection, camera, and UI still bypass it.

Presentation Behaviour:
Agent positions can interpolate. Almost everything else changes in tile or tick steps.

Simulation Dependency:
Renderer layers query `world` directly for tiles, events, mysteries, farms, stockpiles, homes, workshops, history, and settlement data.

Why It Still Feels Discrete:
The player sees a smooth `@` moving over a world that still updates as grid cells, symbols, and tick-driven overlays. The underlying simulation grid remains visually dominant.

Recommended Long-Term Architecture:
Expand the Presentation Engine into multiple presentation domains:

```text
PresentationEngine
  -> AgentPresentation
  -> CameraPresentation
  -> EnvironmentPresentation
  -> FoliagePresentation
  -> WaterPresentation
  -> StructurePresentation
  -> SelectionPresentation
  -> UIPresentation
```

Expected Visual Impact:
Very high. This changes the feel of the whole game, not just villagers.

Estimated Complexity:
High.

Priority:
Critical.

Suggested task:
TASK-101 - Presentation Snapshot Expansion.

### Critical - Camera Is Integer Tile Based

Current Architecture:
Camera state is `camera_x` and `camera_y` in tile coordinates. Panning changes by `CAMERA_STEP` tiles. Visible bounds and screen conversion use integer tile math.

Presentation Behaviour:
The viewport jumps in tile increments. The camera does not ease, coast, or interpolate.

Simulation Dependency:
Camera math is tightly coupled to visible tile bounds and direct tile rendering.

Why It Still Feels Discrete:
Even if villagers move smoothly, the world itself jumps when the camera moves. Integer camera movement makes the tile grid feel like the primary coordinate system.

Recommended Long-Term Architecture:
Introduce `PresentationCamera` with continuous world-space position:

```text
camera_target_tile
  -> camera_target_world
  -> smoothed camera_world_x/y
  -> renderer viewport
```

Keep tile bounds for culling, but render using sub-tile camera offsets.

Expected Visual Impact:
Very high. Camera smoothing often makes an otherwise tile-based game feel dramatically less mechanical.

Estimated Complexity:
Medium to High, because terrain chunk blitting and picking need sub-tile offsets.

Priority:
Critical.

Suggested task:
TASK-102 - Presentation Camera and World-Space Viewport.

### High - Agent Movement Interpolation Restarts From Simulation Updates

Current Architecture:
`PresentationAgent.observe(...)` detects changed simulation tile coordinates and starts interpolation from the current rendered position to the new tile.

Presentation Behaviour:
Movement is smooth between observed tile positions, but the target only changes when simulation updates move the agent.

Simulation Dependency:
Movement timing is still driven by discrete simulation path steps and update cadence.

Why It Still Feels Discrete:
Agents may pause or change target rhythmically based on simulation scheduling. Movement can appear as a series of tile hops with easing rather than a continuous walk intention.

Recommended Long-Term Architecture:
Expose movement intent snapshots from simulation:

```text
agent tile
agent intended path
agent activity
agent movement speed class
```

Presentation should maintain a short visual path queue and consume it at presentation speed. Simulation remains authoritative, but presentation can hide short timing gaps.

Expected Visual Impact:
High. Villagers will feel like they are walking through space rather than being pulled tile to tile.

Estimated Complexity:
Medium.

Priority:
High.

Suggested task:
TASK-103 - Agent Motion Intent and Presentation Path Queues.

### High - No Time-Driven Animation State

Current Architecture:
Agents render as `"@"` symbols. Farms, homes, workshops, stockpiles, animals, and construction render as static glyphs or simple rectangles.

Presentation Behaviour:
There is no walking cycle, idle cycle, work cycle, rest cycle, facing animation, or transition animation.

Simulation Dependency:
Visible activity is represented mostly by `current_action`, `current_goal`, tile type, and UI text.

Why It Still Feels Discrete:
Without animation, the only visible change is position or symbol state. A villager who is alive, thinking, talking, eating, resting, or watching still appears visually frozen unless moving.

Recommended Long-Term Architecture:
Add presentation-owned animation states derived from snapshots:

```text
simulation action/goal/shared moment
  -> presentation animation state
  -> time-driven animation phase
  -> sprite frame selection
```

Expected Visual Impact:
Very high.

Estimated Complexity:
High, especially once sprites arrive.

Priority:
High.

Suggested task:
TASK-104 - Presentation Animation State Machine.

### High - Idle Behaviour Is Visually Static

Current Architecture:
When agents are not moving, presentation render position reaches the target and stops.

Presentation Behaviour:
Idle villagers are perfectly still.

Simulation Dependency:
Idle life depends on simulation social state, but no visual state expresses it.

Why It Still Feels Discrete:
A living village contains many villagers who are not moving at any given moment. If all of them freeze, the settlement feels paused between ticks.

Recommended Long-Term Architecture:
Add visual-only idle motion:

- breathing
- blinking
- weight shifting
- small gaze changes
- tiny social orientation changes
- subtle idle loops tied to shared moments

These must be presentation-only and must never affect decisions or positions.

Expected Visual Impact:
High.

Estimated Complexity:
Medium after animation infrastructure exists.

Priority:
High.

Suggested task:
TASK-105 - Idle Life Presentation.

### High - Weather, Clouds, and Mystery Effects Use Simulation Tick as Animation Clock

Current Architecture:
Cloud shadows, rain particles, foliage highlights, and Strange Lights drift use `world.tick`, integer division, and modulo arithmetic.

Presentation Behaviour:
Effects animate only as simulation ticks advance. When simulation speed changes, effect speed changes. When paused, effects freeze.

Simulation Dependency:
Presentation motion is tied directly to `world.tick`.

Why It Still Feels Discrete:
Atmosphere reveals the simulation clock. Tick division creates visible stepping, especially in slow movement or pulsing effects.

Recommended Long-Term Architecture:
Move atmospheric animation into `EnvironmentPresentation`:

```text
simulation weather state/intensity
  -> presentation weather target
  -> time-driven particles, opacity, drift, clouds
```

Simulation should expose state and intensity only. Presentation should own phase, particle lifetime, opacity interpolation, and movement.

Expected Visual Impact:
High.

Estimated Complexity:
Medium.

Priority:
High.

Suggested task:
TASK-106 - Time-Driven Environmental Presentation.

### High - Renderer Still Queries Gameplay Objects Directly

Current Architecture:
Renderer functions call `world.tile_at`, `world.farm_at`, `world.home_at`, `world.workplace_at`, `world.history`, `world.living_agents`, `world.active_environment_events`, and other gameplay APIs.

Presentation Behaviour:
Only agent drawing has a snapshot boundary. Most draw code is also data extraction code.

Simulation Dependency:
Renderer is coupled to world internals and gameplay collection shapes.

Why It Still Feels Discrete:
The renderer sees the world as tiles and gameplay objects. It has little room to express visual continuity or derived presentation state.

Recommended Long-Term Architecture:
Introduce presentation snapshots per layer:

- `TerrainPresentationSnapshot`
- `VegetationPresentationSnapshot`
- `StructurePresentationSnapshot`
- `EnvironmentPresentationSnapshot`
- `AgentPresentationSnapshot`
- `UIPresentationSnapshot`

Renderer should gradually consume these instead of reaching into `World`.

Expected Visual Impact:
Indirect but very high. This unlocks future visual work.

Estimated Complexity:
High.

Priority:
High.

Suggested task:
TASK-107 - Renderer Snapshot Boundary Audit and Migration.

### Medium - Facing Snaps to Direction Vectors

Current Architecture:
`PresentationAgent` stores facing as `(sign(dx), sign(dy))`.

Presentation Behaviour:
Facing changes instantly when a new tile target appears.

Simulation Dependency:
Facing is derived from tile deltas.

Why It Still Feels Discrete:
Instant facing flips are readable but robotic. Diagonal or rapid path changes make villagers feel like pieces rotating on a board.

Recommended Long-Term Architecture:
Represent facing as presentation state:

- target direction from movement intent
- smoothed orientation
- sprite-facing bucket for final draw
- optional gaze direction while idle

Expected Visual Impact:
Medium to High once sprites exist.

Estimated Complexity:
Medium.

Priority:
Medium.

### Medium - World Coordinates Are Still Primarily Tile Coordinates

Current Architecture:
Renderer functions convert tiles to pixels with `tile * TILE_SIZE`. Screen picking uses `mouse // TILE_SIZE`. Chunk rendering and agent offsets assume tile-space first.

Presentation Behaviour:
Agents have float render positions, but almost every other layer is tile-centered.

Simulation Dependency:
Tile coordinates dominate rendering.

Why It Still Feels Discrete:
The visual composition keeps reaffirming that the world is a square grid.

Recommended Long-Term Architecture:
Keep simulation tile coordinates, but make presentation world-space the default:

```text
simulation tile coordinate
  -> presentation world coordinate
  -> camera transform
  -> screen coordinate
```

Expected Visual Impact:
Medium to High.

Estimated Complexity:
High because it touches camera, picking, chunks, overlays, and sprites.

Priority:
Medium.

### Medium - Terrain Still Mixes Static World and Gameplay Symbols

Current Architecture:
Terrain chunks include terrain plus structures, farms, stockpiles, resources, animals, settlement center symbols, homes, and workshops.

Presentation Behaviour:
Many objects are drawn as static tile symbols during chunk rebuild.

Simulation Dependency:
Chunk cache invalidation depends on gameplay visual cache state.

Why It Still Feels Discrete:
Durable objects pop between symbolic states. Some dynamic or semi-dynamic objects are still visually part of terrain.

Recommended Long-Term Architecture:
Split durable layers more aggressively:

- terrain base
- roads/bridges
- water base
- structures
- vegetation trunks
- foliage overlay
- resources/crops/animals

Let Presentation Objects own animated or changing visual layers.

Expected Visual Impact:
Medium.

Estimated Complexity:
High.

Priority:
Medium.

### Medium - Trees Are Only Partially Presentation-Driven

Current Architecture:
Forest base terrain is cached. Foliage overlay samples smooth seasonal colour but still scans forest tiles and uses tick-modulated highlights.

Presentation Behaviour:
Foliage colour is smooth, but motion is not a true presentation object.

Simulation Dependency:
Foliage is derived directly from tile kind, season, day, and tick.

Why It Still Feels Discrete:
Forest remains tile-shaped and mostly static. Highlight changes are procedural tile overlays rather than continuous tree life.

Recommended Long-Term Architecture:
Create `PresentationTree` or `FoliagePresentation` objects with:

- stable random phase per tree/tile
- wind sway
- seasonal colour target
- leaf particles
- shadow contribution

Expected Visual Impact:
Medium to High.

Estimated Complexity:
Medium.

Priority:
Medium.

### Medium - Water Is Not Yet a Continuous Visual System

Current Architecture:
Water uses terrain rendering and weather transition state. Natural rivers and lakes exist as terrain features.

Presentation Behaviour:
Water does not yet have independent ripple phase, current, shimmer, or shoreline motion.

Simulation Dependency:
Water visuals are mostly tile and weather state.

Why It Still Feels Discrete:
Rivers and lakes are physically better now, but visually static.

Recommended Long-Term Architecture:
Create `WaterPresentation`:

- continuous ripple phase
- local flow direction from river geometry
- shoreline shimmer
- weather-driven surface intensity

Expected Visual Impact:
Medium.

Estimated Complexity:
Medium.

Priority:
Medium.

### Medium - Selection and Inspection Snap to Simulation Tiles

Current Architecture:
Selection uses `world.agent_at(tile_x, tile_y)` and selected agents highlight at `selected_agent.x/y`.

Presentation Behaviour:
Highlights draw around simulation tile positions, not interpolated render positions.

Simulation Dependency:
Selection is gameplay-object based.

Why It Still Feels Discrete:
A moving villager may be drawn between tiles while the selection highlight remains snapped to the destination or current simulation tile.

Recommended Long-Term Architecture:
Add `SelectionPresentation`:

- selected entity id
- interpolated highlight position
- hover position in world-space
- separate gameplay selection from visual highlight

Expected Visual Impact:
Medium.

Estimated Complexity:
Low to Medium.

Priority:
Medium.

### Low - UI and Chronicle Panels Refresh Abruptly

Current Architecture:
History and diagnostics overlays refresh every second and rebuild labels from world state.

Presentation Behaviour:
Panels can jump when refreshed. Chronicle notifications are not presented as animated events; they appear as log entries.

Simulation Dependency:
Overlays read world/history directly.

Why It Still Feels Discrete:
This does not affect the world view as strongly as camera or animation, but it makes information presentation feel mechanical.

Recommended Long-Term Architecture:
Add UI presentation view models:

- recent event feed
- notification queue
- smooth entry fade-in
- stable scroll preservation
- diagnostics refresh decoupled from visual layout

Expected Visual Impact:
Low to Medium.

Estimated Complexity:
Medium.

Priority:
Low.

### Low - Lighting Is Mostly Absent

Current Architecture:
There is no full dynamic lighting system. Cloud shadows exist as overlays.

Presentation Behaviour:
The world lacks time-of-day light change, local glow, warmth, and soft shadows.

Simulation Dependency:
Lighting is not yet a simulation feature, which is good. It can be presentation-led.

Why It Still Feels Discrete:
Without light continuity, scenes lack temporal atmosphere.

Recommended Long-Term Architecture:
Add a presentation-only lighting layer:

- ambient colour target
- weather dimming
- fire/window glow
- mystery glow
- future day/night hooks

Expected Visual Impact:
Medium after sprites and camera smoothing.

Estimated Complexity:
Medium to High.

Priority:
Low for architecture sequencing, higher for final visual mood.

## Performance Observations

Renderer work is still frequently caused by simulation-facing queries:

- `draw_cached_map` compares gameplay visual cache state.
- Visible terrain redraw checks scan tile signatures.
- Foliage overlay scans visible forest tiles every frame.
- Weather and mystery overlays allocate new surfaces every frame.
- UI panels rebuild labels on refresh.
- Renderer diagnostics call several world aggregation functions.

These are not immediate blockers, but they show the Presentation Engine has not yet become the main cache boundary.

Potential architectural improvements:

- Presentation snapshots should be built once per frame and shared by render layers.
- Long-lived presentation objects should own visual phase and cached derived values.
- Renderer layers should consume prepared lists of drawables rather than scanning `World`.
- Environmental overlays should reuse surfaces or particle buffers where practical.
- Diagnostics should be sampled at low frequency and not participate in core presentation state.

## Architectural Review

The Presentation Layer currently sits partially between Simulation and Renderer.

It is correctly placed for:

- agent interpolation
- agent snapshot drawing
- headless compatibility
- removing render-motion state from gameplay agents

The renderer still reaches back into gameplay for:

- terrain tile data
- farms
- construction
- structures
- resources
- animals
- homes
- stockpiles
- workshops
- weather events
- mysteries
- season and day state
- camera bounds
- selection
- panel data
- history and diagnostics

This is expected for the first implementation. It becomes a problem only if future visual work continues adding direct renderer queries instead of expanding presentation snapshots.

## Architectural Recommendations

1. Expand presentation snapshots before adding sprites.

Sprites need stable visual entities, animation state, facing, shadow data, and camera transforms. Adding sprites directly to the current renderer would hard-code too many gameplay dependencies.

2. Build camera presentation next.

Camera smoothing and sub-tile viewport transforms will make the whole world feel less grid-bound.

3. Move atmospheric animation off `world.tick`.

Weather, clouds, particles, and mysteries should use presentation time and simulation-provided target states.

4. Add an animation state machine before detailed artwork.

The project needs states such as idle, walk, work, gather, rest, watch, warm, mourn, and celebrate before it needs final sprites.

5. Split selection presentation from gameplay selection.

The player should select gameplay objects, but highlights should follow presentation positions.

6. Gradually replace renderer world queries with presentation view models.

Do not attempt a risky rewrite. Migrate one layer at a time.

## Suggested Future Roadmap

### TASK-101 - Presentation Snapshot Expansion

Create layer-specific snapshots for agents, environment, camera, selection, and UI. Keep terrain snapshots minimal until camera and sprites require deeper changes.

Priority:
Critical.

### TASK-102 - Presentation Camera and World-Space Viewport

Introduce smoothed continuous camera position, sub-tile viewport offsets, and world-space coordinate helpers.

Priority:
Critical.

### TASK-103 - Agent Motion Intent and Presentation Path Queues

Let presentation consume short movement intentions so visual motion remains continuous even when simulation updates are discrete.

Priority:
High.

### TASK-104 - Presentation Animation State Machine

Introduce time-driven animation state derived from action, goal, shared moment, celebration, visitor state, and mystery reaction.

Priority:
High.

### TASK-105 - Idle Life Presentation

Add presentation-only idle motion and social orientation.

Priority:
High.

### TASK-106 - Time-Driven Environmental Presentation

Move weather, clouds, particles, Strange Lights, fog, and future atmosphere to presentation time.

Priority:
High.

### TASK-107 - Renderer Snapshot Boundary Migration

Audit one renderer layer at a time and replace direct world queries with presentation snapshots.

Priority:
High.

### TASK-108 - Selection and UI Presentation

Make selection highlights, recent history, notifications, and diagnostics visually stable without changing gameplay.

Priority:
Medium.

### TASK-109 - Foliage and Water Presentation Objects

Introduce persistent visual objects for trees and water after camera and environment timing are stable.

Priority:
Medium.

## Long-Term Presentation Vision

The final target should feel like:

```text
Simulation
  decides what exists and what happened

Presentation
  remembers how things are currently appearing
  interpolates toward simulation truth
  owns animation, particles, lighting, camera, and visual rhythm

Renderer
  draws prepared presentation state
```

The simulation should remain deterministic and testable. The Presentation Engine should make that deterministic world feel alive. The renderer should become simpler over time because it no longer needs to interpret gameplay state directly.

The goal is not to hide the grid completely. Automated Colony can remain a tile simulation. The goal is to stop making the grid feel like the only thing that is alive.

## Final Assessment

The current Presentation Engine is a successful foundation, not a complete solution.

The simulation still feels tick-based because:

- the camera is tile-snapped
- agents have no animation or idle life
- atmosphere uses simulation tick as animation time
- most renderer layers query `World` directly
- selection and UI remain simulation-position based
- visual entities are not yet long-lived presentation objects

The next few tasks should widen the Presentation Engine rather than improve individual visuals. Once camera, animation state, environment time, and snapshot boundaries exist, the visual overhaul can add sprites and effects without dragging gameplay logic into the renderer.
