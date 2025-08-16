from typing import Tuple
from utils.decision_engine import compute_positions_for_teams
from constants import DEFAULT_PLAYER_SPEED
from utils.orientation import compute_orientation   # NEW — your new helper file

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
                tx, ty = px, py
            else:
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

            # --- NEW: update orientation before committing new location ---
            team_dir = None
            if hasattr(match, "attacking_dir"):
                team_dir = match.attacking_dir.get(player.team_code)

            player.orientation_deg = compute_orientation(
                pos_xy=(px, py),
                target_xy=(tx, ty) if (tx, ty) != (px, py) else None,
                attacking_dir=team_dir,
                current_deg=player.orientation_deg,
                max_turn_deg_per_tick=None,  # or e.g. 25.0 for gradual turning
            )

            player.update_location((nx, ny, 0.0))

        self.after_decisions(match)

    def check_transition(self, match):
        return None
"""will just house the desicion tree loop I am guessing now run by the states 
Basically we will just take last 2 status' from controller 
check the matrix for a match 
extract the modifiers from that substate 
run the decision trees from there 
execute the actions
update location targets 
trigger_movement
end of loop
redo 60 times a second for smoothness
"""

"""status is determined by the ball mainly// could be its own py file for completeness
each action or event(new) has its own status tag and the player and the location of event
thus comparing it will allow us to determine what should happen next"""

"""events are concept in order to remove the blackhole caused by using a ball based fsm. essentially reducing the need for states to 
need to trigger each other or ever interact with each other as that is messy
try event penalty_given scrum-called etc
these are essentially anything done by a referee blowing there whistle and saves the ball having to worry 
about adavantage etc as that is handled by other modules"""