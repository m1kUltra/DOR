# matchEngine/states/maul.py
from states.base_state import BaseState
from utils.formations import get_maul_ring, place_defensive_setpiece

class MaulState(BaseState):
    def __init__(self, anchor_xy: tuple[float,float], attack_team: str):
        super().__init__()
        self.name = "maul"
        self.anchor_xy = anchor_xy
        self.attack_team = attack_team
        self._seeded = False
        self._locks_until = 2

    def before_decisions(self, match):
        # dead ball at anchor while forming
        match.ball.release()
        ax, ay = self.anchor_xy
        match.ball.location = (ax, ay, 0.0)

        if self._seeded:
            return

        # Attack binders around ellipse; defense counter-front
        atk = get_maul_ring(self.anchor_xy, self.attack_team, {"count": 6, "bias": "tight"}, match)
        def_team_obj = match.team_b if self.attack_team == 'a' else match.team_a
        deff = place_defensive_setpiece(def_team_obj, {"type": "maul", "anchor": self.anchor_xy}, match)
        for p, tgt in {**atk, **deff}.items():
            p.current_action = p.current_action or "bind_maul"
            setattr(p, "action_meta", {"to": tgt, "lock": True})

        self._seeded = True

    def after_decisions(self, match):
        # After a brief form time, recycle to 9 like a ruck-lite
        if self.ticks_in_state < 3:
            return
        team = match.team_a if self.attack_team == 'a' else match.team_b
        nine = team.get_player_by_rn(9) or team.get_player_by_sn(9)
        if nine:
            match.ball.holder = f"{nine.sn}{self.attack_team}"
            match.ball.location = nine.location

        # unlock
        if self.ticks_in_state >= self._locks_until:
            for p in match.players:
                meta = getattr(p, "action_meta", {}) or {}
                if meta.get("lock"):
                    meta["lock"] = False
                    setattr(p, "action_meta", meta)

    def check_transition(self, match):
        if match.ball.is_held() and self.ticks_in_state >= 3:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
