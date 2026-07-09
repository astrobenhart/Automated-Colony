from __future__ import annotations

from dataclasses import dataclass, field


def presentation_id_for(agent) -> str:
    return getattr(agent, "agent_id", None) or getattr(agent, "name", "")


def presentation_key_for(agent) -> str:
    return getattr(agent, "agent_id", None) or f"object:{id(agent)}"


@dataclass(frozen=True)
class PresentationAgentSnapshot:
    agent_id: str
    name: str
    tile_x: int
    tile_y: int
    render_x: float
    render_y: float
    role: str
    current_action: str
    current_goal: str
    facing: tuple[int, int] = (0, 1)


@dataclass(frozen=True)
class PresentationSnapshot:
    agents: tuple[PresentationAgentSnapshot, ...]
    render_order: tuple[str, ...] = ("agents",)
    frame_index: int = 0


@dataclass(frozen=True)
class PresentationFrameState:
    frame_index: int = 0
    time_delta: float = 0.0


@dataclass
class PresentationAgent:
    agent_id: str
    name: str
    tile_x: int
    tile_y: int
    render_x: float
    render_y: float
    from_x: float
    from_y: float
    target_x: float
    target_y: float
    progress: float = 1.0
    facing: tuple[int, int] = (0, 1)
    role: str = ""
    current_action: str = "Idle"
    current_goal: str = "Explore"

    @classmethod
    def from_agent(cls, agent) -> "PresentationAgent":
        agent_id = presentation_id_for(agent)
        x = float(getattr(agent, "x", 0))
        y = float(getattr(agent, "y", 0))
        return cls(
            agent_id=agent_id,
            name=getattr(agent, "name", agent_id),
            tile_x=getattr(agent, "x", 0),
            tile_y=getattr(agent, "y", 0),
            render_x=x,
            render_y=y,
            from_x=x,
            from_y=y,
            target_x=x,
            target_y=y,
            role=getattr(agent, "role", ""),
            current_action=getattr(agent, "current_action", "Idle"),
            current_goal=getattr(agent, "current_goal", "Explore"),
        )

    def observe(self, agent) -> None:
        next_x = getattr(agent, "x", self.tile_x)
        next_y = getattr(agent, "y", self.tile_y)
        self.name = getattr(agent, "name", self.name)
        self.role = getattr(agent, "role", self.role)
        self.current_action = getattr(agent, "current_action", self.current_action)
        self.current_goal = getattr(agent, "current_goal", self.current_goal)

        if (next_x, next_y) == (self.tile_x, self.tile_y):
            return

        dx = next_x - self.tile_x
        dy = next_y - self.tile_y
        if dx or dy:
            self.facing = (sign(dx), sign(dy))

        self.from_x = self.render_x
        self.from_y = self.render_y
        self.target_x = float(next_x)
        self.target_y = float(next_y)
        self.tile_x = next_x
        self.tile_y = next_y
        self.progress = 0.0

    def advance(self, time_delta: float, tiles_per_second: float) -> None:
        if self.progress >= 1.0:
            self.render_x = self.target_x
            self.render_y = self.target_y
            return

        distance = max(0.001, abs(self.target_x - self.from_x) + abs(self.target_y - self.from_y))
        self.progress = min(1.0, self.progress + max(0.0, time_delta) * tiles_per_second / distance)
        eased = smoothstep(self.progress)
        self.render_x = self.from_x + (self.target_x - self.from_x) * eased
        self.render_y = self.from_y + (self.target_y - self.from_y) * eased

    def snapshot(self) -> PresentationAgentSnapshot:
        return PresentationAgentSnapshot(
            agent_id=self.agent_id,
            name=self.name,
            tile_x=self.tile_x,
            tile_y=self.tile_y,
            render_x=self.render_x,
            render_y=self.render_y,
            role=self.role,
            current_action=self.current_action,
            current_goal=self.current_goal,
            facing=self.facing,
        )


@dataclass
class PresentationScene:
    """Root of presentation-owned visual state.

    The scene observes simulation state and owns long-lived presentation objects.
    Gameplay systems should not depend on this class.
    """

    agents: dict[str, PresentationAgent] = field(default_factory=dict)
    last_snapshot: PresentationSnapshot = field(default_factory=lambda: PresentationSnapshot(agents=()))
    render_order: tuple[str, ...] = ("agents",)
    frame_state: PresentationFrameState = field(default_factory=PresentationFrameState)

    def sync_world(self, world) -> None:
        living_agents = [agent for agent in getattr(world, "agents", ()) if getattr(agent, "alive", False)]
        live_ids = {presentation_key_for(agent) for agent in living_agents}
        for stale_id in set(self.agents) - live_ids:
            del self.agents[stale_id]

        for agent in living_agents:
            agent_key = presentation_key_for(agent)
            presentation_agent = self.agents.get(agent_key)
            if presentation_agent is None:
                self.agents[agent_key] = PresentationAgent.from_agent(agent)
            else:
                presentation_agent.observe(agent)

        self.last_snapshot = self.snapshot()

    def update(self, world, time_delta: float, tiles_per_second: float) -> PresentationSnapshot:
        self.frame_state = PresentationFrameState(
            frame_index=self.frame_state.frame_index + 1,
            time_delta=max(0.0, time_delta),
        )
        self.sync_world(world)
        for agent in self.agents.values():
            agent.advance(time_delta, tiles_per_second)
        self.last_snapshot = self.snapshot()
        return self.last_snapshot

    def snapshot(self) -> PresentationSnapshot:
        return PresentationSnapshot(
            agents=tuple(agent.snapshot() for agent in self.agents.values()),
            render_order=self.render_order,
            frame_index=self.frame_state.frame_index,
        )

    def snapshot_world(self, world) -> PresentationSnapshot:
        self.sync_world(world)
        return self.last_snapshot


class PresentationEngine(PresentationScene):
    """Compatibility name for the first presentation root."""


def smoothstep(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def sign(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0
