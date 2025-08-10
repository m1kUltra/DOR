# matchEngine/states/base_state.py
from typing import Tuple
from utils.decision_engine import compute_positions_for_teams
from constants import DEFAULT_PLAYER_SPEED

class BaseState:
    def __init__(self):
        self.name = "base"
        self.ticks_in_state = 0

    def on_enter(self, match): pass
    def before_decisions(self, match): pass
    def after_decisions(self, match): pass

    def update(self, match):
        self.ticks_in_state += 1

        self.before_decisions(match)

        # batch: decide -> spacing resolve -> move
        decisions = compute_positions_for_teams(match, self)

        for player, (action, target) in decisions.items():
            player.current_action = action

        for player, (_, target) in decisions.items():
            px, py, _ = player.location
            tx, ty, _ = target
            speed = player.attributes.get('physical', {}).get('speed', DEFAULT_PLAYER_SPEED)
            step = max(0.0, float(speed)) * float(match.tick_rate)

            dx, dy = (tx - px), (ty - py)
            d2 = dx*dx + dy*dy
            if d2 > 0.0 and step * step < d2:
                import math
                k = step / math.sqrt(d2)
                nx, ny = px + dx * k, py + dy * k
            else:
                nx, ny = tx, ty
            player.update_location((nx, ny, 0.0))

        self.after_decisions(match)

    def check_transition(self, match):
        return None
