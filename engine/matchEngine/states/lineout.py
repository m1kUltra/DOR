# matchEngine/states/lineout.py

from states.base_state import BaseState
from constants import TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y
from utils.formations import (
    get_lineout_formation,
    place_defensive_setpiece,
    get_maul_ring,
)

class LineoutState(BaseState):
    def __init__(self, mark_x: float, touch_y: float, throw_to: str, call: dict | None = None):
        super().__init__()
        self.name = "lineout"
        # clamp to the touch line
        touch_y = TOUCHLINE_BOTTOM_Y if touch_y <= (TOUCHLINE_BOTTOM_Y + 0.1) else TOUCHLINE_TOP_Y
        self.mark = (mark_x, touch_y, 0.0)
        self.throw_to = throw_to  # 'a' or 'b'
        # default call if none provided
        self.call = call or {"zone": "mid", "length": "mid", "outcome": "off_top", "numbers": 7}
        self._seeded = False
        self._locks_until = 2

    def before_decisions(self, match):
        match.ball.release()
        match.ball.location = self.mark

        if self._seeded:
            return

        mark_xy = (self.mark[0], self.mark[1])

        # Attack lineout formation (includes pods, hooker, 9/10/backs infield)
        lo = get_lineout_formation(mark_xy, self.throw_to, self.call, match)  # {"targets":{Player:(x,y,0)}, "meta":{...}}
        atk_targets = lo.get("targets", {})
        self._lo_meta = lo.get("meta", {})

        # Defense mirrors / 10m rule etc.
        def_team = 'b' if self.throw_to == 'a' else 'a'
        def_targets = place_defensive_setpiece(def_team, {"type": "lineout", "mark": mark_xy, **self.call}, match)

        for p, tgt in {**atk_targets, **def_targets}.items():
            p.current_action = p.current_action or "shape"
            setattr(p, "action_meta", {"to": tgt, "lock": True})

        self._seeded = True

    def after_decisions(self, match):
        # after 2 ticks, execute the outcome
        if self.ticks_in_state < 2:
            return

        outcome = (self.call or {}).get("outcome", "off_top")
        if outcome == "maul":
            # seed a maul around the jumper catch point
            anchor = self._lo_meta.get("catch_xy") or (self.mark[0] + (1.0 if self._lo_meta.get("zone") == "front" else 3.0), self.mark[1] + (1.5 if self.mark[1] < 35.0 else -1.5))
            ring_targets = get_maul_ring(anchor, self.throw_to, {"count": 6, "bias": "tight"}, match)
            for p, tgt in ring_targets.items():
                p.current_action = p.current_action or "bind_maul"
                setattr(p, "action_meta", {"to": tgt, "lock": True})

            # Transition into MaulState
            from states.maul import MaulState
            return  # let check_transition handle it below

        # default off-top: give ball to 9 (existing simple behavior)
        team = match.team_a if self.throw_to == 'a' else match.team_b
        nine = team.get_player_by_rn(9) or (team.get_player_by_sn(9) if team.get_player_by_sn(9) else None)
        if nine:
            match.ball.holder = f"{nine.sn}{self.throw_to}"
            match.ball.location = nine.location

        # release locks after placement window
        if self.ticks_in_state >= self._locks_until:
            for p in match.players:
                meta = getattr(p, "action_meta", {}) or {}
                if meta.get("lock"):
                    meta["lock"] = False
                    setattr(p, "action_meta", meta)

    def check_transition(self, match):
        # If we seeded a maul, move into MaulState once placements are done
        if getattr(self, "_lo_meta", None) and (self.call or {}).get("outcome") == "maul" and self.ticks_in_state >= 2:
            from states.maul import MaulState
            anchor = self._lo_meta.get("catch_xy") or (self.mark[0], self.mark[1])
            return MaulState(anchor_xy=anchor, attack_team=self.throw_to)

        if match.ball.is_held() and self.ticks_in_state >= 2:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
