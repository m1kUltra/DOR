# states/ruck.py
from .base_state import BaseState
from constants import (
    FORWARDS, RUCK_RADIUS, RUCK_FORM_TICKS, RUCK_CONTEST_TICKS,
    RECYCLE_FAST_TICKS, RECYCLE_SLOW_TICKS, OFFSIDE_PENALTY_ENFORCE,
    GATE_DEPTH, RUCK_GATE_WIDTH
)
from utils.ruck_utils import compute_last_feet_line, is_legal_entry, nearest_n

class RuckState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "ruck"
        self._phase_tick = 0
        self._recycle_wait = 0

    def set_anchor(self, xyz):
        self._anchor = xyz

    def ruck_commit_plan(self, match) -> dict[str, list[int]]:
        ax, ay = match.ruck_meta["anchor"]
        A = [p for p in match.team_a.squad if p.rn in FORWARDS]
        B = [p for p in match.team_b.squad if p.rn in FORWARDS]
        return {"a": [p.sn for p in nearest_n(A, (ax,ay), 3)],
                "b": [p.sn for p in nearest_n(B, (ax,ay), 3)]}

    def enforce_offside_ruck(self, match) -> None:
        if not OFFSIDE_PENALTY_ENFORCE: return
        rm = match.ruck_meta
        ax, ay = rm["anchor"]
        last_line = ax - rm["attack_dir"] * GATE_DEPTH
        attack_side = 'a' if rm["attack_dir"] > 0 else 'b'
        defense = match.team_b if attack_side == 'a' else match.team_a
        for p in defense.squad:
            px = p.location[0]
            if (px - last_line) * rm["attack_dir"] > 0.0:
                match.pending_penalty = {"mark": (ax, ay), "to": attack_side, "reason": "offside_ruck"}
                return

    def resolve_ruck_outcome(self, match, a_commit: int, b_commit: int) -> tuple[str, str]:
        if a_commit - b_commit >= 1: return ('a', 'fast')
        if b_commit - a_commit >= 1: return ('b', 'fast')
        adv = match.advantage
        if adv and adv.get("to") in ('a','b'):
            return (adv["to"], "slow")
        roll = match.rng.randf("ruck_tie", match.tick_count, key=int(match.ruck_meta["anchor"][0]*100))
        return (('a' if roll < 0.5 else 'b'), 'slow')

    def post_ruck_reorg(self, match, winner_team: str, ball_speed: str) -> None:
        team = match.team_a if winner_team=='a' else match.team_b
        nine = team.get_player_by_rn(9) or team.get_player_by_sn(9)
        if nine:
            match.ball.holder = f"{nine.sn}{winner_team}"
            match.ball.location = nine.location
        else:
            ax, ay = match.ruck_meta["anchor"]
            cand = min(team.squad, key=lambda p: (p.location[0]-ax)**2 + (p.location[1]-ay)**2)
            match.ball.holder = f"{cand.sn}{winner_team}"
            match.ball.location = cand.location

    def before_decisions(self, match):
        rm = match.ruck_meta
        if not rm:
            # seed fallback from ball
            ax, ay, _ = match.ball.location
            dir_ = +1.0
            match.ruck_meta = {
                "anchor": (ax, ay), "phase":"forming", "since_tick": match.tick_count,
                "last_feet_line": ax - dir_ * GATE_DEPTH, "winner": None,
                "ball_speed": None, "attack_dir": dir_,
            }
            rm = match.ruck_meta

        # dead ball at anchor
        ax, ay = rm["anchor"]
        match.ball.release()
        match.ball.location = (ax, ay, 0.0)

        # tackler off‑feet countdown
        for p in match.players:
            if getattr(p, "_down_ticks", 0) > 0:
                p.state_flags["is_on_feet"] = False
                p._down_ticks -= 1
            else:
                p.state_flags["is_on_feet"] = True

        # mark radius + legality
        for p in match.players:
            px, py, _ = p.location
            d2 = (px-ax)**2 + (py-ay)**2
            p.state_flags["in_ruck_radius"] = d2 <= (RUCK_RADIUS**2)
            team = match.team_a if p.team_code == 'a' else match.team_b
            p.state_flags["entered_from_gate"] = is_legal_entry((px,py), (ax,ay), team.tactics.get("attack_dir", +1.0))

        # Assign join targets through the gate (lock them)
        plan = self.ruck_commit_plan(match)
        for side, sns in plan.items():
            team = match.team_a if side=='a' else match.team_b
            dir_ = team.tactics.get("attack_dir", +1.0)
            # stagger through the gate
            offsets = [(-0.5, 0.0), (-0.8, +1.0), (-0.8, -1.0)]
            for i, sn in enumerate(sns):
                p = team.get_player_by_sn(sn)
                if not p: continue
                gx = ax - dir_ * abs(offsets[i % len(offsets)][0])
                gy = ay + offsets[i % len(offsets)][1]
                p.current_action = "join_ruck"
                setattr(p, "action_meta", {"to": (gx, gy, 0.0), "lock": True})

    def after_decisions(self, match):
        rm = match.ruck_meta
        if not rm: return
        phase = rm["phase"]

        if phase == "forming":
            self._phase_tick += 1
            if self._phase_tick >= RUCK_FORM_TICKS:
                # count legal commits within radius
                ax, ay = rm["anchor"]
                a_legal = sum(1 for p in match.team_a.squad if p.state_flags["in_ruck_radius"] and p.state_flags["entered_from_gate"] and p.rn in FORWARDS)
                b_legal = sum(1 for p in match.team_b.squad if p.state_flags["in_ruck_radius"] and p.state_flags["entered_from_gate"] and p.rn in FORWARDS)
                rm["_a_legal"] = a_legal
                rm["_b_legal"] = b_legal
                rm["phase"] = "contest"
                rm["since_tick"] = match.tick_count
                self._phase_tick = 0
            return

        if phase == "contest":
            self._phase_tick += 1
            self.enforce_offside_ruck(match)  # whistle if needed
            if self._phase_tick >= RUCK_CONTEST_TICKS:
                winner, speed = self.resolve_ruck_outcome(match, rm.get("_a_legal",0), rm.get("_b_legal",0))
                rm["winner"] = winner
                rm["ball_speed"] = speed
                rm["phase"] = "recycle"
                self._recycle_wait = RECYCLE_FAST_TICKS if speed == "fast" else RECYCLE_SLOW_TICKS
                self._phase_tick = 0
            return

        if phase == "recycle":
            self._recycle_wait -= 1
            if self._recycle_wait <= 0:
                self.post_ruck_reorg(match, rm["winner"], rm["ball_speed"])
                match.ruck_meta = None
                from .open_play import OpenPlayState
                match.current_state = OpenPlayState()

    def check_transition(self, match):
        return None  # handled inline
