# matchEngine/states/open_play.py

from states.base_state import BaseState
from utils.decision_engine import process_decision

class OpenPlayState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "open_play"
        self.ticks_in_state = 0

    def update(self, match):
        self.ticks_in_state += 1

        for player in match.players:
            action, target = process_decision(
                player, self, match.ball,
                match.team_a if player.team_code == 'a' else match.team_b,
                match.team_b if player.team_code == 'a' else match.team_a,
                pitch=match.pitch
            )
            player.current_action = action
            player.update_location(target)

        match.ball.update(match)

    def check_transition(self, match):
        """
        Simulate a transition back to ruck if someone enters contact.
        For now, if any player chooses 'enter_contact', we go to a ruck.
        """
        if any(p.current_action == "enter_contact" for p in match.players):
            from matchEngine.states.ruck import RuckState
            return RuckState()
        return None
