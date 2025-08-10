# matchEngine/states/scrum.py

from states.base_state import BaseState

class ScrumState(BaseState):
    def __init__(self, mark_x: float, mark_y: float, put_in: str):
        super().__init__()
        self.name = "scrum"
        self.mark = (mark_x, mark_y, 0.0)
        self.put_in = put_in  # 'a' or 'b'

    def before_decisions(self, match):
        # dead ball at mark
        match.ball.release()
        match.ball.location = self.mark

    def after_decisions(self, match):
        # quick-resolution scrum: after 2 ticks, give to 9 of put-in team
        if self.ticks_in_state < 2:
            return
        team = match.team_a if self.put_in == 'a' else match.team_b
        nine = team.get_player_by_rn(9) or (team.get_player_by_sn(9) if team.get_player_by_sn(9) else None)
        if nine:
            match.ball.holder = f"{nine.sn}{self.put_in}"
            match.ball.location = nine.location

    def check_transition(self, match):
        # when someone picks up the ball (holder set), go open play
        if match.ball.is_held() and self.ticks_in_state >= 2:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
