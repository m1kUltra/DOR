# matchEngine/player.py

class Player:
    def __init__(self, name, sn, rn, team_code, location=(0.0, 0.0, 0.0), attributes=None, height=None, weight=None):
        self.name = name
        self.sn = sn  # Squad Number
        self.rn = rn  # Role Number (actual field role)
        self.team_code = team_code  # 'a' or 'b'
        self.location = location  # (x, y, z) in meters
        self.height = height
        self.weight = weight

        self.attributes = attributes or {
            'mental': {},
            'physical': {},
            'technical': {}
        }

        self.current_action = None  # e.g., 'run', 'pass', etc.

    def update_location(self, new_location):
        """Update the 3D position of the player."""
        self.location = new_location

    def make_decision(self, game_state, ball, team, opposition_team):
        """
        Determines the next action or position based on:
        - Current game state (e.g., 'ruck', 'scrum')
        - Ball position and holder
        - Team in possession
        - Own role number (rn)
        """
        # Placeholder logic — this will call into decision_engine later
        pass

    def perform_action(self, action):
        """
        Executes an action (like pass, kick, run).
        Each action can live in its own module in /actions.
        """
        self.current_action = action
        # Action logic would be handled elsewhere
        pass

    def __repr__(self):
        return f"<Player {self.sn}{self.team_code} ({self.name}) at {self.location}>"
