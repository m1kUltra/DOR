# matchEngine/states/lineout.py

from states.base_state import BaseState
from constants import TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y

class LineoutState(BaseState):
    def __init__(self, mark_x: float, touch_y: float, throw_to: str):
        super().__init__()
        self.name = "lineout"
        # clamp to the touch line
        touch_y = TOUCHLINE_BOTTOM_Y if touch_y <= (TOUCHLINE_BOTTOM_Y + 0.1) else TOUCHLINE_TOP_Y
        self.mark = (mark_x, touch_y, 0.0)
        self.throw_to = throw_to  # 'a' or 'b'

    def before_decisions(self, match):
        match.ball.release()
        match.ball.location = self.mark

    def after_decisions(self, match):
        # after 2 ticks, award ball to throwing team's 9 (simple)
        if self.ticks_in_state < 2:
            return
        team = match.team_a if self.throw_to == 'a' else match.team_b
        nine = team.get_player_by_rn(9) or (team.get_player_by_sn(9) if team.get_player_by_sn(9) else None)
        if nine:
            match.ball.holder = f"{nine.sn}{self.throw_to}"
            match.ball.location = nine.location

    def check_transition(self, match):
        if match.ball.is_held() and self.ticks_in_state >= 2:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
