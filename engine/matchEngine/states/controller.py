# states/controller.py
from typing import Dict, Tuple, Optional
import event 
from states.ActionMatrix import ACTION_MATRIX ,SAME # keep your import as-is

WILDCARD = "_"            # <- underscore means "any last_action"

DEFAULT_FALLBACK = SAME  # your safe default

class StateController:
    def __init__(self, match):
        self.match = match
        self.status = ("restart.kick_off",
                       getattr(match.ball, "location", (50.0, 35.0, 0.0)),
                       getattr(match.ball, "holder", None))

    def tick(self) -> None:
        if self._event_check():
            return
        self._status_check()

    def _event_check(self) -> bool:
        evt = event.get_event()
        if not evt:
            return False
        self.status = evt
        event.clear_event()
        return True

    def _status_check(self) -> None:
        ball = self.match.ball
        curr = getattr(ball, "status", None)       # {"action","holder","location"}
        last = getattr(ball, "last_status", None)
        if not curr or not last or _same_snapshot(curr, last):
            return

        last_action = last.get("action")
        curr_action = curr.get("action")

        state_tag = _resolve_state_tag(last_action, curr_action)

        if state_tag == SAME:
            state_tag = self.status[0] if isinstance(self.status, tuple) else DEFAULT_FALLBACK

        loc = curr.get("location", getattr(ball, "location", (0.0, 0.0)))
        holder = curr.get("holder", getattr(ball, "holder", None))
        self.status = (state_tag, loc, holder)

        # optional: advance snapshot here if you don't do it in ball.update()
        # ball.last_status = curr


def _resolve_state_tag(last_action: Optional[str], curr_action: Optional[str]) -> str:

    
    """
    Priority:
      1) exact   : (last, curr)
      2) wildcard: ("_", curr)
      3) default : DEFAULT_FALLBACK
    """
    # exact match first
    tag = ACTION_MATRIX.get((last_action, curr_action))
    if tag:
        return tag

    # wildcard on last
    tag = ACTION_MATRIX.get((WILDCARD, curr_action))
    if tag:
        return tag

    # nothing matched -> safe default
    return DEFAULT_FALLBACK


def _same_snapshot(a: dict, b: dict) -> bool:
    # compare only promised fields; if you hit jitter later add an epsilon here
    return (
        a.get("action")   == b.get("action") and
        a.get("holder")   == b.get("holder") and
        a.get("location") == b.get("location")
    )
