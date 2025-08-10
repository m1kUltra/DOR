# matchEngine/states/ruck.py
from states.base_state import BaseState
from constants import FORWARDS

class RuckState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "ruck"
        self._anchor = None  # where contact occurred

    def on_enter(self, match):  # optional if you call it on transition later
        pass

    def before_decisions(self, match):
        # lock ball at last location as ruck anchor
        if self._anchor is None:
            self._anchor = match.ball.location
        # make sure ball is loose at ruck
        match.ball.release()
        match.ball.location = self._anchor

    def after_decisions(self, match):
        # after some beats, recycle to one side based on support numbers
        if self.ticks_in_state < 3:
            return

        ax, ay, _ = self._anchor
        # count nearby supporters by team (forwards weighted a bit)
        def nearby_score(team_code: str):
            score = 0.0
            for p in match.players:
                if p.team_code != team_code: continue
                px, py, _ = p.location
                if (px - ax)**2 + (py - ay)**2 <= 9.0:  # within 3m
                    score += 1.5 if p.rn in FORWARDS else 1.0
            return score

        a_score = nearby_score('a')
        b_score = nearby_score('b')

        winner = 'a' if a_score >= b_score else 'b'
        team = match.team_a if winner == 'a' else match.team_b

        # give to 9 if exists, else nearest teammate
        nine = team.get_player_by_rn(9)
        if nine:
            match.ball.holder = f"{nine.sn}{winner}"
            match.ball.location = nine.location
        else:
            # nearest teammate to anchor
            cand = min(
                (p for p in team.squad),
                key=lambda p: (p.location[0]-ax)**2 + (p.location[1]-ay)**2
            )
            match.ball.holder = f"{cand.sn}{winner}"
            match.ball.location = cand.location

    def check_transition(self, match):
        # when ball is picked up by someone, go back to open play
        if match.ball.is_held() and self.ticks_in_state >= 3:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
