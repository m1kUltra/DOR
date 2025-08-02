# matchEngine/states/ruck.py

from states.base_state import BaseState
from utils.decision_engine import process_decision

class RuckState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "ruck"
        self.ticks_in_state = 0

    def update(self, match):
        self.ticks_in_state += 1

        # Let each player make a decision (positioning based on ruck logic)
        for player in match.players:
            action, target = process_decision(
                player, self, match.ball,
                match.team_a if player.team_code == 'a' else match.team_b,
                match.team_b if player.team_code == 'a' else match.team_a,
                pitch=match.pitch
            )
            player.current_action = action
            player.update_location(target)

        # Ball follows holder, if any
        match.ball.update(match)

    def check_transition(self, match):
        """
        Example: After 5 ticks, ball is recycled and we go to open play.
        You can later make this depend on player actions or turnover chance.
        """
        if self.ticks_in_state >= 5:
            from matchEngine.states.open_play import OpenPlayState
            return OpenPlayState()
        return None
