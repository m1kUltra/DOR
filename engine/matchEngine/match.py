# matchEngine/Match.py
import json

from setup import setup_match
from states.base_state import BaseState
from utils.logger import log_tick
import time 
class Match:
    def __init__(self, db_path, team_a_id, team_b_id):
        self.tick_count = 0
        self.match_time = 0.0  # seconds
        self.tick_rate = 0.05  # 1s per tick (your choice)

        # --- set-piece/event flags (init once here) ---
        self.pending_scrum = None      # {"x": float, "y": float, "put_in": "a"|"b"}
        self.pending_lineout = None    # {"x": float, "y": float, "throw_to": "a"|"b"}
        self.last_touch_team = None    # "a" or "b"

        # build teams/players/ball/pitch
        self.team_a, self.team_b, self.players, self.ball, self.pitch = setup_match(
            db_path, team_a_id, team_b_id
        )

        self.current_state: BaseState = None
        self.set_initial_state()

    def set_initial_state(self):
        from states.restart import RestartState
        self.current_state = RestartState()

    def update(self):
        """Advance the game by one tick."""
        self.tick_count += 1
        self.match_time += self.tick_rate

        # 1) State handles per-tick decisions + movement
        self.current_state.update(self)

          
       
        # 2) Ball follows holder
        self.ball.update(self)
                # 2.1) central routing for set-piece flags created by actions/ball
        if getattr(self, "pending_lineout", None):
            data = self.pending_lineout
            self.pending_lineout = None
            from states.lineout import LineoutState
            self.current_state = LineoutState(data["x"], data["y"], data["throw_to"])
            return  # skip the rest of this tick to avoid double processing

        if getattr(self, "pending_scrum", None):
            data = self.pending_scrum
            self.pending_scrum = None
            from states.scrum import ScrumState
            self.current_state = ScrumState(data["x"], data["y"], data["put_in"])
            return


        # 2.5) possession & scoring checks
        self._sync_possession()
        self._check_scoring()

        # 3) transition
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
            "state": self.current_state.name
        }
    # add inside class Match:

    def get_player_by_code(self, code: str):
        """e.g. '10a' -> Player or None"""
        if not code: return None
        sn = int(code[:-1]); team_code = code[-1]
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
        """Very simple try detection: holder grounds beyond opposition tryline."""
        if not self.ball.holder:
            return
        holder = self.get_player_by_code(self.ball.holder)
        if not holder:
            return
        x, y, _ = holder.location
        # Team A attacks towards x+, Team B towards x-
        if holder.team_code == 'a' and x >= 100.0:
            # try to A
            # TODO: increment score, etc.
            # reset to restart
            from states.restart import RestartState
            self.current_state = RestartState()
            return
        if holder.team_code == 'b' and x <= 0.0:
            # try to B
            from states.restart import RestartState
            self.current_state = RestartState()
            return


# python -m matchEngine.match  (if you ever run as module)
if __name__ == "__main__":
    match = Match("tmp/temp.db", team_a_id=2, team_b_id=1)
    match.run(ticks=1000)
