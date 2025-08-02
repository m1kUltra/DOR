# matchEngine/states/restart.py

from states.base_state import BaseState
from utils.decision_engine import process_decision

class RestartState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "restart"
        self.ticks_in_state = 0

    def update(self, match):
        self.ticks_in_state += 1

        # On first tick, place the ball at halfway and give it to 10a
        if self.ticks_in_state == 1:
            match.ball.location = (50.0, 35.0, 0.0)  # Midfield
            match.ball.holder = "10a"

        # Players position themselves according to restart logic
        for player in match.players:
            action, target = process_decision(
                player, self, match.ball,
                match.team_a if player.team_code == 'a' else match.team_b,
                match.team_b if player.team_code == 'a' else match.team_a,
                pitch=match.pitch
            )
            player.current_action = action
            player.update_location(target)

    def check_transition(self, match):
        # After 2 ticks, transition into open play
        if self.ticks_in_state >= 2:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
