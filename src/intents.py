from __future__ import annotations

from dataclasses import dataclass, field


WALK_INTENT = "walk"


@dataclass(frozen=True)
class AgentIntent:
    intent_id: str
    kind: str
    label: str
    target: tuple[int, int] | None = None
    path: tuple[tuple[int, int], ...] = ()
    source_action: str = ""
    source_goal: str = ""


@dataclass
class IntentQueue:
    max_length: int = 4
    items: list[AgentIntent] = field(default_factory=list)

    def replace(self, intents: list[AgentIntent] | tuple[AgentIntent, ...]) -> None:
        self.items = list(intents[:self.max_length])

    def peek(self) -> AgentIntent | None:
        return self.items[0] if self.items else None

    def clear(self) -> None:
        self.items.clear()

    def __len__(self) -> int:
        return len(self.items)


def movement_intent_for(agent) -> AgentIntent | None:
    target = getattr(agent, "current_target", None)
    path = tuple(getattr(agent, "current_path", ()) or ())
    if target is None and not path:
        return None

    current_position = (getattr(agent, "x", 0), getattr(agent, "y", 0))
    intent_path = (current_position, *path)
    if target is not None and (not intent_path or intent_path[-1] != target):
        intent_path = (*intent_path, target)

    if len(intent_path) <= 1:
        return None

    source_action = getattr(agent, "current_action", "")
    source_goal = getattr(agent, "current_goal", "")
    label = _movement_label(source_action, source_goal, target)
    intent_id = f"{WALK_INTENT}:{target}:{intent_path}:{source_action}:{source_goal}"
    return AgentIntent(
        intent_id=intent_id,
        kind=WALK_INTENT,
        label=label,
        target=target,
        path=intent_path,
        source_action=source_action,
        source_goal=source_goal,
    )


def intent_queue_for(agent) -> IntentQueue:
    queue = IntentQueue()
    movement_intent = movement_intent_for(agent)
    if movement_intent is not None:
        queue.replace([movement_intent])
    return queue


def _movement_label(source_action: str, source_goal: str, target: tuple[int, int] | None) -> str:
    if source_action:
        return source_action
    if source_goal:
        return f"Walk for {source_goal}"
    if target is not None:
        return f"Walk to {target[0]},{target[1]}"
    return "Walk"
