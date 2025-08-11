# matchEngine/states/open_play.py
from states.base_state import BaseState
from constants import TACKLE_RANGE, TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y, MAX_CHASERS
from actions import dispatch
from utils.logger import log_law

from constants import MAX_CHASERS  # keep existing
from actions import dispatch
from utils.collision import detect_tackle_event, resolve_tackle

class OpenPlayState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "open_play"
        self.phase = "attack"     # "attack" | "defense" | "kick_chase" | "loose_ball"
        self.kick_meta = None     # {"team","start_t","type"}
        self.kick_chase_ticks = 0

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
        evt = detect_tackle_event(match)
        if evt:
            resolve_tackle(match, evt["tackler"], evt["holder"], evt["anchor"])
            # immediate transition to RuckState this tick
            from states.ruck import RuckState
            match.current_state = RuckState()
            return
    def after_decisions(self, match):
        # If a kick was chosen this tick, enter kick-chase sub-state
        kick_pickers = [
            p for p in match.players
            if p.current_action == "kick" and getattr(p, "action_meta", {}).get("kick_tuple")
        ]
        if kick_pickers and self.phase != "kick_chase":
            kicker = kick_pickers[0]
            ktype, v0_hint, lateral = kicker.action_meta["kick_tuple"]
            self.phase = "kick_chase"
            self.kick_meta = {"team": kicker.team_code, "start_t": match.match_time, "type": ktype}
            self.kick_chase_ticks = 0

        # execute ball-affecting actions (contact, catch, kick, pass)
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

        # Kick-chase sub-state behavior
        if self.phase == "kick_chase":
            self.kick_chase_ticks += 1

            # exit conditions: caught, dead/inactive flight, or timeout
            if match.ball.is_held() or not match.ball.in_flight or self.kick_chase_ticks > 80:
                self.phase = "attack"
                self.kick_meta = None
                self.kick_chase_ticks = 0
                return

            # Assign chasers from the kicking team
            team_code = self.kick_meta["team"]
            kicking_team = match.team_a if team_code == 'a' else match.team_b
            others = sorted(
                kicking_team.squad,
                key=lambda p: ((p.location[0] - bx) ** 2 + (p.location[1] - by) ** 2, p.rn, p.sn)
            )
            chasers = others[:MAX_CHASERS]
            for c in chasers:
                c.current_action = "chase"
                setattr(c, "action_meta", {"to": (bx, by, 0.0)})

            # Nearest defender moves to field the kick
            opp = match.team_b if team_code == 'a' else match.team_a
            nearest = min(
                opp.squad,
                key=lambda p: ((p.location[0] - bx) ** 2 + (p.location[1] - by) ** 2)
            )
            nearest.current_action = "field_kick"
            setattr(nearest, "action_meta", {"to": (bx, by, 0.0)})

    def check_transition(self, match):
        # If ball released (tackle), enter ruck
        if not match.ball.is_held():
            from states.ruck import RuckState
            return RuckState()
        return None
