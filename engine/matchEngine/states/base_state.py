# states/base_state.py
from typing import Tuple, Any
from states.controller import StateController
from choice.choice_controller import select as choose_select
from actions.action_controller import do_action
from states import restart, scoring, nudge
from team.team_controller import sync_flags
#from set_pieces.place_kick import do_conversion
# NEW imports


class BaseState:
    def __init__(self, match):
        self.match = match
        self.controller = StateController(match)

    def tick(self) -> Tuple[str, Any, Any]:
        # 1) decide current state/event
        self.controller.tick()
        tag, loc, ctx = self.controller.status  # (tag_or_event, location, context)
        
        # keep team/holder flags in sync BEFORE any handler uses them
        sync_flags(self.match)

        # 2) state-specific handlers
        for mod in (restart, scoring, nudge):
            handler = getattr(mod, "maybe_handle", None)
            if handler and handler(self.match, tag, loc, ctx):
                # CRITICAL: push ball state forward so controller can see changes next frame
                self.match.ball.update(self.match)
                sync_flags(self.match)
                return (tag, loc, ctx)

        # 3) open-play (default) flow
        calls = choose_select(self.match, (tag, loc, ctx))
        if calls:
            if isinstance(calls, tuple):
                calls = [calls]
            for pid, action, _loc_ignored, target in calls:
                # use the actor's current position, not the state/ball location
                loc_p = self.match.get_player_by_code(pid).location
                do_action(self.match, pid, action, loc_p, target)

        # 4) advance physics every tick + resync flags
        self.match.ball.update(self.match)
        sync_flags(self.match)
     
        return (tag, loc, ctx)




