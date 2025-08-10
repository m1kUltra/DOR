# matchEngine/Match.py
import json
import time

from setup import setup_match
from states.base_state import BaseState
from utils.logger import log_tick, log_routing, log_law  # include law + routing logs
from utils.rng import DeterministicRNG  # deterministic RNG
from utils.restarts import map_event_to_flag
from utils.advantage import start as adv_start, tick as adv_tick


class Match:
    def __init__(self, db_path, team_a_id, team_b_id, seed: int | None = None, debug: dict | None = None):  # seed + debug
        # --- tick + clocks ---
        self.tick_count = 0
        self.match_time = 0.0  # seconds (global wall clock)
        self.tick_rate = 0.05  # seconds per tick

        # --- deterministic RNG ---
        self.seed = seed if seed is not None else 123456  # default seed
        self.rng = DeterministicRNG(self.seed)            # channelled RNG

        # --- telemetry toggles (cheap guards inside logger funcs) ---
        self.debug = {"decisions": True, "routing": True, "laws": True}
        if debug is not None:
            self.debug.update(debug)

        # --- period/clock ---
        self.period = {"half": 1, "time": 0.0, "added_time": 0.0, "stoppage_accum": 0.0, "status": "live"}

        # --- restart/advantage & set-piece flags ---
        self.pending_penalty = None   # {"mark": (x,y), "to": "a"|"b", "reason": str}
        self.pending_restart = None   # {"type": "kickoff|22_do|goal_line_do|post_score", "to": "a"|"b"}
        self.pending_scrum = None     # {"x": float, "y": float, "put_in": "a"|"b", "reason": "knock_on|forward_pass|reset"}
        self.pending_lineout = None   # {"x": float, "y": float, "throw_to": "a"|"b", "reason": "touch|50_22"}
        self.advantage = None         # {"type":"knock_on|penalty","to":"a"|"b","start_t":float,"start_x":float,"start_y":float,"timer_s":0.0,"meters":0.0}

        # --- misc context ---
        self.last_touch_team = None   # "a" or "b"
        self.last_restart_to = None   # who restarts next (kickoff/dropout)
        self.scoreboard = {"a": 0, "b": 0}

        # build teams/players/ball/pitch
        self.team_a, self.team_b, self.players, self.ball, self.pitch = setup_match(
            db_path, team_a_id, team_b_id
        )

        self.current_state: BaseState = None
        self.set_initial_state()

    def set_initial_state(self):
        from states.restart import RestartState
        self.current_state = RestartState()

    # --- centralized router so all flag transitions are observable ---
    def route_by_flags(self) -> bool:
        if self.period["status"] == "fulltime":
            return False
        """Consume one highest-priority flag and transition state. Return True if routed."""
        # PRIORITY: penalty > restart > scrum > lineout
        # PENALTY (stub for Phase 1)
        if self.pending_penalty:
            data = self.pending_penalty
            self.pending_penalty = None
            log_routing(self.tick_count, self, "pending_penalty", data)
            # TODO: add PenaltyState later; for now, fall back to RestartState placeholder
            from states.restart import RestartState
            self.current_state = RestartState()
            return True

        # RESTARTS (kickoff, 22 dropout, goal-line dropout, post-score)
        if self.pending_restart:
            data = self.pending_restart
            self.pending_restart = None
            self.last_restart_to = data.get("to")
            log_routing(self.tick_count, self, "pending_restart", data)
            # Halftime resume: if we were at halftime and consuming a kickoff, flip to 2H
            if self.period.get("status") == "halftime" and data.get("type") == "kickoff":
                prev = dict(self.period)
                self.period = {"half": 2, "time": 0.0, "added_time": 0.0, "stoppage_accum": 0.0, "status": "live"}
                log_routing(self.tick_count, self, "period_change", {"from": prev, "to": self.period})
            from states.restart import RestartState
            self.current_state = RestartState()  # Phase 1: generic restart
            return True

        # SCRUM
        if self.pending_scrum:
            data = self.pending_scrum
            self.pending_scrum = None
            log_routing(self.tick_count, self, "pending_scrum", data)
            from states.scrum import ScrumState
            self.current_state = ScrumState(data["x"], data["y"], data["put_in"])
            return True

        # LINEOUT
        if self.pending_lineout:
            data = self.pending_lineout
            self.pending_lineout = None
            log_routing(self.tick_count, self, "pending_lineout", data)
            from states.lineout import LineoutState
            self.current_state = LineoutState(data["x"], data["y"], data["throw_to"])
            return True

        return False

    def update(self):
        if self.period["status"] == "fulltime":
    # still tick wall‑clock so serializers keep advancing if you want
            self.match_time += self.tick_rate
            return
        """Advance the game by one tick."""
        self.tick_count += 1

        # 1) State handles per-tick decisions + movement
        self.current_state.update(self)

        # 2) Ball follows holder / flight physics
        self.ball.update(self)

        # 3) Centralized routing for set-piece flags created by actions/ball
        if self.route_by_flags():
            return  # skip the rest to avoid double processing this tick

        # 4) Possession & scoring checks
        self._sync_possession()
        self._check_scoring()

        # 5) Match clock (halves, halftime, fulltime)
        self.match_clock_tick()

        # 6) Advantage overlay processing
        self.update_advantage()

        # 7) State transition check
        next_state = self.current_state.check_transition(self)
        if next_state:
            self.current_state = next_state

        log_tick(self.tick_count, self)

    def run(self, ticks=1000, realtime=True, speed=1.0):
        for _ in range(ticks):
            t0 = time.time()
            self.update()
            print(json.dumps(self.serialize_tick()), flush=True)
            if realtime:
                # Aim for wall-clock pacing ~= tick_rate / speed
                budget = self.tick_rate / max(speed, 1e-6)
                delay = budget - (time.time() - t0)
                if delay > 0:
                    time.sleep(delay)

    def serialize_tick(self):
        return {
            "tick": self.tick_count,
            "time": self.match_time,
            "scoreboard": self.scoreboard,
            "ball": {
                "location": self.ball.location,
                "holder": self.ball.holder
            },
            "players": [
                {
                    "name": p.name,
                    "sn": p.sn,
                    "rn": p.rn,
                    "team_code": p.team_code,
                    "action": p.current_action,
                    "location": p.location
                }
                for p in self.players
            ],
            "state": self.current_state.name,
            "period": self.period,
            "advantage": self.advantage
        }

    # add inside class Match:

    def get_player_by_code(self, code: str):
        """e.g. '10a' -> Player or None"""
        if not code:
            return None
        sn = int(code[:-1])
        team_code = code[-1]
        team = self.team_a if team_code == 'a' else self.team_b
        return team.get_player_by_sn(sn)

    def _sync_possession(self):
        """Set team.in_possession flags based on ball holder."""
        a, b = False, False
        if self.ball.holder:
            a = self.ball.holder.endswith('a')
            b = self.ball.holder.endswith('b')
        self.team_a.set_possession(a)
        self.team_b.set_possession(b)

    def _check_scoring(self):
        if not self.ball.holder or self.period["status"] != "live":
            return
        holder = self.get_player_by_code(self.ball.holder)
        if not holder:
            return
        x, _, _ = holder.location

        # Team A attacks to x+, Team B to x-
        if holder.team_code == 'a' and x >= 100.0:
            # Try to A
            self.scoreboard["a"] += 5
            self.pending_restart = {"type": "post_score", "to": "b"}  # B kicks off
            return

        if holder.team_code == 'b' and x <= 0.0:
            # Try to B
            self.scoreboard["b"] += 5
            self.pending_restart = {"type": "post_score", "to": "a"}  # A kicks off
            return


    # --- CLOCK & ADVANTAGE -------------------------------------------------
    def match_clock_tick(self) -> None:
        """Advance the base clock and manage halftime/fulltime boundaries."""
        # advance global wall clock
        self.match_time += self.tick_rate

        half_cap = 40 * 60  # 2400s per half
        # Only run half clock when live
        if self.period["status"] == "live" and self.period["half"] in (1, 2):
            t = self.period["time"] + self.tick_rate
            self.period["time"] = t

            # halftime boundary
            if self.period["half"] == 1 and t >= half_cap + self.period["added_time"]:
                prev = dict(self.period)
                self.period["status"] = "halftime"
                # schedule kickoff to start 2H next
                self.pending_restart = {"type": "kickoff", "to": "b"}
                log_routing(self.tick_count, self, "period_change", {"from": prev, "to": dict(self.period)})

            # full-time boundary
            if self.period["half"] == 2 and t >= half_cap + self.period["added_time"]:
                prev = dict(self.period)
                self.period["status"] = "fulltime"
                log_routing(self.tick_count, self, "period_change", {"from": prev, "to": dict(self.period)})

    def update_advantage(self) -> None:
        if not self.advantage:
            return
        team = self.team_a if self.advantage["to"] == 'a' else self.team_b
        attack_dir = float(team.tactics.get("attack_dir", +1.0))
        bx = self.ball.location[0]

        new_adv, flag_dict, outcome = adv_tick(
            self.advantage,
            match_time=self.match_time,
            ball_x=bx,
            attack_dir=attack_dir
        )

        if outcome == "realized":
            log_law(self.tick_count, "advantage_realized", dict(self.advantage), match=self)
        elif outcome == "called_back":
            log_law(self.tick_count, "advantage_called_back", dict(self.advantage), match=self)
            if flag_dict:
                if "pending_penalty" in flag_dict:  self.pending_penalty  = flag_dict["pending_penalty"]
            
                if "pending_scrum"   in flag_dict:  self.pending_scrum    = flag_dict["pending_scrum"]
               

        self.advantage = new_adv



# python -m matchEngine.match  (if you ever run as module)
if __name__ == "__main__":
    match = Match("tmp/temp.db", team_a_id=2, team_b_id=1, seed=42, debug={"decisions": True, "routing": True, "laws": True})
    match.run(ticks=1000)
