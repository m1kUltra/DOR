import json
import time
from utils.core.logger import dump_tick_json
from setup import setup_match
from states.base_state import BaseState

# utils (per your tree)
from utils.core.logger import log_tick , dump_tick_json


      # detect_* live here
      # award_try etc.

# whistle layer (non-instant flags → next state)



class Match:
    """
    Ultra-thin orchestrator:
      - Delegates per-tick decisions & ball physics to BaseState.tick()
      - Keeps clocks, advantage, scoring, and serialisation
      - Converts law outcomes into a single whistle event via event.set_event(...)
    """

    def __init__(self, db_path, team_a_id, team_b_id, seed: int | None = None, debug: dict | None = None):
        # tick / time
        self.tick_count = 0
        self.match_time = 0.0
        self.tick_rate  = 0.05

        
        # debug toggles (only used inside logger helpers)
        self.debug = {"decisions": True, "routing": True, "laws": True}
        if debug is not None:
            self.debug.update(debug)

        # period/clock
        self.period = {"half": 1, "time": 0.0, "added_time": 0.0, "stoppage_accum": 0.0, "status": "live"}

        # context flags kept for laws/advantage; routing is via events.set_event ##will proabbly be dropped 
        self.advantage = None
        self.last_touch_team = None
        self.last_restart_to = None
        self.last_kick = None
        self.conversion_ctx = None
        self.scoreboard = {"a": 0, "b": 0}
        self.offside = 0 #x point in whhcih the offside line is set 
        self.lineout_roles: tuple[str, str] | None = None
        # optional ruck meta placeholder
        

        # build world
        self.team_a, self.team_b, self.players, self.ball, self.pitch = setup_match(
            db_path, team_a_id, team_b_id)
        self.state = BaseState(self)
        # single state engine (handles decisions, action dispatch, and ball.update())
       

    # ----------------------------
    # main loop
    # ----------------------------
    #TODO move this to anywhere but match
    def get_player_by_code(self, code: str):
        """e.g. '10a' -> Player or None"""
        if not code:
            return None
        rn = int(code[:-1])
        team_code = code[-1]
        team = self.team_a if team_code == 'a' else self.team_b
        return team.get_player_by_rn(rn)
    
     # 
   
    # matchEngine/match.py
    def run(self, ticks=1000, realtime=True, speed=1.0):
         
        for _ in range(ticks):
            t0 = time.time()
            if self.tick_count >= 1000: break

            # advance clocks here (don’t rely on BaseState to do it)
            self.tick_count += 1
            self.match_time += self.tick_rate
            self.period["time"] += self.tick_rate

            self.state.tick()
           
            # emit JSON to STDOUT — no bare except swallowing errors
         
                
                

            dump_tick_json(self)
            #import sys, math; tr=self.ball.transit or {}; pace=(tr.get("speed") if tr.get("type")=="linear" else ((math.hypot(tr["target"][0]-tr["start"][0], tr["target"][1]-tr["start"][1]) / tr["T"]) if tr.get("type")=="parabola" and tr.get("T") else None)); print(f"DBG target={self.ball.target} loc={self.ball.location} pace={pace}", file=sys.stderr, flush=True)
            
            if realtime:
                budget = self.tick_rate / max(speed, 1e-6)
                delay = budget - (time.time() - t0)
                if delay > 0:
                    time.sleep(delay)




if __name__ == "__main__":
    match = Match("tmp/temp.db", team_a_id=2, team_b_id=1, seed=42,
                  debug={"decisions": True, "routing": True, "laws": True})
    match.run(ticks=1000)


    """"whole point of match.py be as small as possible - do nothing
    as main  initilise everything through setup.py
    has the main
    takes the clock for holding time 
    counts the clicks compared to itself 
    runs the loop but the loop is just pointing to base_state and that takes care of evrything in game laws scoring movemenet choices actions 
    all, sapwned from this not a match responsibility
    calls from the logger the method that sends the info to the front
    
    """
    """  import sys, math
            code = "10a"
            p = next((pl for pl in self.players if f"{pl.sn}{pl.team_code}" == code), None)
            bx, by, bz = self.ball.location
            if p:
                px, py, pz = p.location
                d = math.hypot(bx - px, by - py)
                print(f"DBG {code} loc={p.location} act={getattr(p,'current_action',None)} dist_to_ball={d:.2f} ball_z={bz:.2f}", file=sys.stderr, flush=True)
            else:
                print(f"DBG {code} not found", file=sys.stderr, flush=True)
"""