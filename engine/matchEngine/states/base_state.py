# states/base_state.py
from typing import Tuple, Any
from states.controller import StateController
from choice.choice_controller import select as choose_select
from actions.action_controller import do_action
from states import restart, scoring, nudge, ruck, open_play
from team.team_controller import sync_flags

class BaseState:
    def __init__(self, match):
        self.match = match
        self.controller = StateController(match)

    def tick(self) -> Tuple[str, Any, Any]:
        # 1) drive controller once
        self.controller.tick()
        tag, loc, ctx = self.controller.status

        # keep flags sane before anyone looks at them
        sync_flags(self.match)

        # 2) HARD handlers: own actions + early return
        for mod in (restart, scoring, nudge, ruck):
            handler = getattr(mod, "maybe_handle", None)
            if handler and handler(self.match, tag, loc, ctx):
                self.match.ball.update(self.match)
                sync_flags(self.match)
                return self.controller.status

        # 3) SOFT glue (open_play): may change ball/tag, but NO actions
        op_handler = getattr(open_play, "maybe_handle", None)
        if op_handler and op_handler(self.match, tag, loc, ctx):
            # tag might have changed (e.g., to open_play.scramble) → re-tick
            self.controller.tick()
            tag, loc, ctx = self.controller.status

        # 4) Execute choices **only** for open_play.*
        if isinstance(tag, str) and (tag == "open_play" or tag.startswith("open_play.")):
            calls = choose_select(self.match, (tag, loc, ctx)) or []
            if isinstance(calls, tuple):
                calls = [calls]
            for pid, action, _ignored, target in calls:
                loc_p = self.match.get_player_by_code(pid).location
                do_action(self.match, pid, action, loc_p, target)

        # 5) single physics step + resync
        self.match.ball.update(self.match)
        sync_flags(self.match)
        return self.controller.status
