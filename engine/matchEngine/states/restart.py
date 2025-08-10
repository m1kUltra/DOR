# matchEngine/states/restart.py

from states.base_state import BaseState

class RestartState(BaseState):
    def __init__(self):
        super().__init__()
        self.name = "restart"
        self._initialized = False

    def before_decisions(self, match):
        """
        One-time kickoff setup:
        - place ball at halfway
        - give it to Team A's fly-half (RN=10) if present
        """
        if self._initialized:
            return

        # Ball at midfield
        match.ball.location = (50.0, 35.0, 0.0)

        # Prefer RN lookup so we don't assume SN==RN
        p10a = match.team_a.get_player_by_rn(10)
        if p10a:
            match.ball.holder = f"{p10a.sn}a"
        else:
            # Fallback: try SN 10 on Team A; else loose ball at halfway
            fallback = match.team_a.get_player_by_sn(10)
            match.ball.holder = f"{fallback.sn}a" if fallback else None

        self._initialized = True

    # Movement/positioning is handled by BaseState.update() via decision engine.

    def check_transition(self, match):
        # After 2 ticks, go to open play
        if self.ticks_in_state >= 2:
            from states.open_play import OpenPlayState
            return OpenPlayState()
        return None
