# matchEngine/Match.py
import json 

from setup import setup_match
from states.base_state import BaseState
from utils.decision_engine import process_decision
from utils.logger import log_tick


class Match:
    def __init__(self, db_path, team_a_id, team_b_id):
        self.tick_count = 0
        self.match_time = 0.0  # seconds
        self.tick_rate = 0.1  # 10 ticks per second

        self.team_a, self.team_b, self.players, self.ball, self.pitch = setup_match(db_path, team_a_id, team_b_id)



        # Game starts in open play or kickoff
        self.current_state: BaseState = None
        self.set_initial_state()

    def set_initial_state(self):
        """Determine the initial state of play."""
        # You could use 'restarts' or 'kickoff' logic here
        from states.restart import RestartState
        self.current_state = RestartState()

    def update(self):
        """Advance the game by one tick."""
        self.tick_count += 1
        self.match_time += self.tick_rate

        # Let the current state update players/ball
        self.current_state.update(self)

        # Players make decisions
        for player in self.players:
            player.make_decision(
                game_state=self.current_state,
                ball=self.ball,
                team=self.team_a if player.team_code == 'a' else self.team_b,
                opposition_team=self.team_b if player.team_code == 'a' else self.team_a
            )

        # Possibly update ball, check possession, handle turnovers, etc.
        self.ball.update(self)

        # Evaluate if state needs to change
        next_state = self.current_state.check_transition(self)
        if next_state:
            self.current_state = next_state
        log_tick(self.tick_count, self)
    def run(self, ticks=1000):
        for _ in range(ticks):
            self.update()
            packet = json.dumps(self.serialize_tick())
            print(json.dumps(self.serialize_tick()), flush=True)  # <-- no prefix


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

#python3 -m engine.matchEngine.match
if __name__ == "__main__":
    match = Match("tmp/temp.db", team_a_id=2, team_b_id=1)
    match.run(ticks=1000)
