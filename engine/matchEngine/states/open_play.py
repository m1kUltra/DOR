# matchEngine/states/open_play.py
from states.base_state import BaseState
from constants import TACKLE_RANGE, TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y
from actions import dispatch
from utils.logger import log_law

class OpenPlayState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "open_play"

    def before_decisions(self, match):
        # tackle trigger
        if not match.ball.holder:
            return
        holder = match.get_player_by_code(match.ball.holder)
        if not holder:
            return
        hx, hy, _ = holder.location

        # closest defender within tackle range
        nearest = None
        best_d2 = None
        for p in match.players:
            if p.team_code == holder.team_code:
                continue
            px, py, _ = p.location
            d2 = (px - hx)**2 + (py - hy)**2
            if best_d2 is None or d2 < best_d2:
                best_d2 = d2
                nearest = p
        if nearest and best_d2 is not None and best_d2 <= (TACKLE_RANGE * TACKLE_RANGE):
            nearest.current_action = "tackle"
            holder.current_action = "enter_contact"  # dispatcher will drop ball

    def after_decisions(self, match):
        # execute ball-affecting actions
        for p in match.players:
            code = f"{p.sn}{p.team_code}"
            if match.ball.holder == code or p.current_action in ("enter_contact", "catch", "kick", "pass"):
                dispatch(p, match)

        # into touch → set flag; router will consume next
        bx, by, _ = match.ball.location
        if by <= TOUCHLINE_BOTTOM_Y or by >= TOUCHLINE_TOP_Y:
            log_law(
                match.tick_count,
                "into_touch",
                {"x": bx, "y": by, "last_touch_by": match.last_touch_team},
                match=match
            )
            throw_to = 'b' if match.last_touch_team == 'a' else 'a'
            match.pending_lineout = {"x": bx, "y": by, "throw_to": throw_to, "reason": "touch"}
            return

    def check_transition(self, match):
        # If ball released (tackle), enter ruck
        if not match.ball.is_held():
            from states.ruck import RuckState
            return RuckState()
        return None
