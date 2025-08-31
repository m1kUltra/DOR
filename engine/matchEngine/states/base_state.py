# states/base_state.py
from typing import Tuple, Any
from states.controller import StateController
from choice.choice_controller import select as choose_select
from actions.action_controller import do_action
from states import restart, scoring, nudge, ruck, open_play
from team.team_controller import sync_flags
#from states import offside  # optional

class BaseState:
    def __init__(self, match):
        self.match = match
        self.controller = StateController(match)

    def tick(self) -> Tuple[str, Any, Any]:
        # 1) decide current state/event
        self.controller.tick()
        tag, loc, ctx = self.controller.status

        # keep flags in sync BEFORE handlers use them
        sync_flags(self.match)
        # offside.update_flags(self.match, tag, loc, ctx)  # optional

        # 2) HARD state-specific handlers (these can own their actions)
        for mod in (restart, scoring, nudge, ruck):
            handler = getattr(mod, "maybe_handle", None)
            if handler and handler(self.match, tag, loc, ctx):
                self.match.ball.update(self.match)
                sync_flags(self.match)
                return (tag, loc, ctx)

        # 2.5) SOFT glue: open_play (do NOT short-circuit the tick)
        op_handler = getattr(open_play, "maybe_handle", None)
        if op_handler and op_handler(self.match, tag, loc, ctx):
            # something like pass_error/line_break/turnover was set
            self.match.ball.update(self.match)
            sync_flags(self.match)
            # re-evaluate the controller so tag reflects the new action now
            self.controller.tick()
            tag, loc, ctx = self.controller.status

        # 3) Run choices (centralized)
        calls = choose_select(self.match, (tag, loc, ctx)) or []
        if isinstance(calls, tuple):
            calls = [calls]
        for pid, action, _loc_ignored, target in calls:
            loc_p = self.match.get_player_by_code(pid).location
            do_action(self.match, pid, action, loc_p, target)

        # 4) advance physics every tick + resync flags
        self.match.ball.update(self.match)
        sync_flags(self.match)
        return (tag, loc, ctx)
