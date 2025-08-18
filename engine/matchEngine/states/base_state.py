# states/base_state.py
from typing import Tuple, Any
from states.controller import StateController
from choice.choice_controller import select as choose_select
from actions.action_controller import do_action

# NEW imports
from states.restart import RESTART_TAGS, KICK_OFF, kickoff_now

class BaseState:
    def __init__(self, match):
        self.match = match
        self.controller = StateController(match)

    def tick(self) -> Tuple[str, Any, Any]:
        # 1) decide current state/event
        self.controller.tick()
        tag, loc, ctx = self.controller.status  # (tag_or_event, location, context)
        
        # --- NEW: handle restarts inline, then get out of the way ---
        if isinstance(tag, str) and tag in RESTART_TAGS:
            if tag == KICK_OFF:
                
                # ctx (event.team) is the receiving side if provided; fallback to last_restart_to or 'b'
                to = ctx if isinstance(ctx, str) else (getattr(self.match, "last_restart_to", None) or "b")
                kickoff_now(self.match, to=to)
                
            # optional: advance ball physics a hair this tick
            self.match.ball.update(self.match)
            return (tag, loc, ctx)

        # 2) open-play (default) flow
        calls = choose_select(self.match, self.controller.status )
        if calls:
            if isinstance(calls, tuple):
                calls = [calls]
            for pid, action, _loc_ignored, target in calls:
                # use the actor's current position, not the state/ball location
                loc = self.match.get_player_by_code(pid).location
                do_action(self.match, pid, action, loc, target)

        self.match.ball.update(self.match)
        return (tag, loc, ctx)
