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

        # optional ruck meta placeholder
        

        # build world
        self.team_a, self.team_b, self.players, self.ball, self.pitch = setup_match(
            db_path, team_a_id, team_b_id)
        self.state = BaseState(self)
        # single state engine (handles decisions, action dispatch, and ball.update())
       

    # ----------------------------
    # main loop
    # ----------------------------


        # 

    # matchEngine/match.py
    def run(self, ticks=1000, realtime=True, speed=1.0):
        for _ in range(ticks):
            t0 = time.time()

            # advance clocks here (don’t rely on BaseState to do it)
            self.tick_count += 1
            self.match_time += self.tick_rate
            self.period["time"] += self.tick_rate

            self.state.tick()
            print(self.state)
            # emit JSON to STDOUT — no bare except swallowing errors
            dump_tick_json(self)

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