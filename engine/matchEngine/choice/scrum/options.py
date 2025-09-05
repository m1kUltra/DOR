"""Surface human decisions for scrum phases."""
from typing import List, Tuple
from actions.action_controller import do_action
from .out import plan as out_plan
import event

Option = Tuple[str, str]  # (label, value)


def get_options(match, state_tuple) -> List[Option]:
    """Return available option tuples for the current scrum state."""
    tag = state_tuple[0] if isinstance(state_tuple, (list, tuple)) else None
    if tag == "scrum.stable":
        return [("Out", "out")]
    if tag == "scrum.out":
        return [("Run", "run"), ("Pass", "pass")]
    return []


def _push_event(match, next_tag: str, loc, ctx) -> None:
    try:
        if hasattr(event, "push"):
            event.push(match, next_tag, loc, ctx)
        elif hasattr(event, "emit"):
            event.emit(match, next_tag, loc, ctx)
        else:
            setattr(match, "next_state_tag", (next_tag, loc, ctx))
    except Exception:
        setattr(match, "next_state_tag", (next_tag, loc, ctx))


def apply_choice(match, state_tuple, choice: str) -> None:
    """Apply a user choice for scrum states."""
    tag = state_tuple[0] if isinstance(state_tuple, (list, tuple)) else None
    loc = state_tuple[1] if len(state_tuple) > 1 else None
    ctx = state_tuple[2] if len(state_tuple) > 2 else None

    if tag == "scrum.stable" and choice == "out":
        _push_event(match, "scrum.out", loc, ctx)
    elif tag == "scrum.out" and choice in ("run", "pass"):
        calls = out_plan(match, state_tuple, choice) or []
        for pid, action, loc0, target in calls:
            do_action(match, pid, action, loc0, target)