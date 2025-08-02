# matchEngine/states/base_state.py

class BaseState:
    def __init__(self):
        self.name = "base"

    def update(self, match):
        """
        Called every tick. Used to update player positioning,
        check ball status, influence AI logic, etc.
        """
        raise NotImplementedError("State must implement `update()`")

    def check_transition(self, match):
        """
        Check if conditions have changed enough to move to another state.
        Return a new state instance, or None to stay in this one.
        """
        return None
