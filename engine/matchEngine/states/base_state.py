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

        # Decide once
        decisions = compute_positions_for_teams(match, self)

        # Apply actions + meta
        for player, bundle in decisions.items():
            # bundle is (action, target, meta?) where target can be None (e.g., kick)
            action = bundle[0]
            target = bundle[1] if len(bundle) > 1 else None
            meta   = bundle[2] if len(bundle) > 2 else {}
            player.current_action = action
            setattr(player, "action_meta", meta)

        # Move everyone toward their targets (if any)
        for player, bundle in decisions.items():
            target = bundle[1] if len(bundle) > 1 else None

            px, py, _ = player.location
            if target is None:
                # No movement target (e.g., kick) -> stay put this tick
                tx, ty = px, py
            else:
                # target is (x, y, z) or (x, y)
                tx = target[0]
                ty = target[1]

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