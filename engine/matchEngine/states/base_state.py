# states/base_state.py
from typing import Tuple, Any, Optional
from states.controller import StateController
from .choice.choice_controller import choice_controller
from actions.action_controller import do_actions

class BaseState:
    def __init__(self, match):
        self.match = match
        self.controller = StateController(match)

    def tick(self) -> Tuple[str, Any, Any]:
        # 1) controller decides state tuple
        self.controller.tick()
        state_tuple = self.controller.status  # (tag_or_event, location, context)

        # 2) decision -> (location, action, target)
        choice = choice_controller.select(self.match, state_tuple)

        # 3) run actions (side-effects only), then update ball physics/position
        do_actions(self.match, state_tuple, choice)
        self.match.ball.update(self.match)

        return state_tuple

"""
new plan for base_state
1. run controller
which will return a state

then we run desicion_controller based on state each state as its own parameters and constraints probably. needs an overhaul
anyway desicon controller will return a (location, action, target) each tick target is target location which can be the same as their existing one
(either desicion_controller or base state will trigger actions ) 
end of tick
"""
