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
            
        }

        self.action = None  # e.g., 'run', 'pass', etc.
        # Phase 3: transient flags (reset each tick)
        self.state_flags = {
    "being_tackled": False,
    "tackling": False,
    "off_feet": False,
    "in_scrum": False,
    "dummy_half": False,
    "first_receiver": False,  # (typo: usually spelled receiver)
    "in_ruck": False,
    "in_maul": False,
    "backfield":False,
    "has_ball":False,
    
}

        self.orientation_deg = None
    def update_location(self, new_location):
        """Update the 3D position of the player."""
        self.location = new_location

  

    def update_action(self, action):
        """
        Executes an action (like pass, kick, run).
        Each action can live in its own module in /actions.
        """
        self.current_action = action
        # Action logic would be handled elsewhere
        pass
    
    def __repr__(self):
        return f"<Player {self.sn}{self.team_code} ({self.name}) at {self.location}>"
    

