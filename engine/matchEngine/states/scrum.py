# matchEngine/states/scrum.py

from states.base_state import BaseState
from utils.formations import (
    get_scrum_formation,
    place_backs_exit_shape,
    place_defensive_setpiece,
)

class ScrumState(BaseState):
    def __init__(self, mark_x: float, mark_y: float, put_in: str, exit_call: str = "10_exit"):
        super().__init__()
        self.name = "scrum"
        self.mark = (mark_x, mark_y, 0.0)
        self.put_in = put_in  # 'a' or 'b'
        self.exit_call = exit_call
        self._seeded = False
        self._locks_until = 2  # ticks to keep players “locked” to targets

    def before_decisions(self, match):
        # dead ball at mark
        match.ball.release()
        match.ball.location = self.mark

        if self._seeded:
            return

        # --- Compute attacking & defending targets ---
        mark_xy = (self.mark[0], self.mark[1])
        attack_team = self.put_in
        defend_team = 'b' if attack_team == 'a' else 'a'

        scr_targets = get_scrum_formation(mark_xy, attack_team, match)  # {Player: (x,y,0)}
        backs_targets = place_backs_exit_shape(self.exit_call, attack_team, mark_xy, match)  # {Player: (x,y,0)}
        def_targets = place_defensive_setpiece(defend_team, {"type": "scrum", "mark": mark_xy, "put_in": attack_team}, match)

        # Merge and assign meta targets (lock for a couple of ticks)
        for p, tgt in {**scr_targets, **backs_targets, **def_targets}.items():
            p.current_action = p.current_action or "shape"
            setattr(p, "action_meta", {"to": tgt, "lock": True})

        self._seeded = True

    def after_decisions(self, match):
        # quick-resolution scrum: after 2 ticks, give to 9 of put-in team (existing behavior)
        if self.ticks_in_state < 2:
            return
        team = match.team_a if self.put_in == 'a' else match.team_b
        nine = team.get_player_by_rn(9) or (team.get_player_by_sn(9) if team.get_player_by_sn(9) else None)
        if nine:
            match.ball.holder = f"{nine.sn}{self.put_in}"
            match.ball.location = nine.location

        # release locks after placement window
        if self.ticks_in_state >= self._locks_until:
            for p in match.players:
                meta = getattr(p, "action_meta", {}) or {}
                if meta.get("lock"):
                    meta["lock"] = False
                    setattr(p, "action_meta", meta)

    def check_transition(self, match):
        # when someone picks up the ball (holder set), go open play
        if match.ball.is_held() and self.ticks_in_state >= 2:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
