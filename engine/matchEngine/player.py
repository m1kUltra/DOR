# matchEngine/player.py

class Player:
    def __init__(self, name, sn, rn, team_code, location=(0.0, 0.0, 0.0), attributes=None, height=None, weight=None):
        self.name = name
        self.sn = sn  # Squad Number
        self.rn = rn  # Role Number (actual field role)
        self.team_code = team_code  # 'a' or 'b'
        self.height = height
        self.weight = weight
        self.location = tuple(location)
        self.target   = None              # (x, y, z) or None
         # fallback pace
        self.arrive_radius = 0.5          # meters; tweak per role

        attrs = attributes or {}
        self.attributes = attrs

        pace_attr = attrs.get("pace")
        if pace_attr is not None:
            self.max_speed_mps = 5 + 5 * ((pace_attr - 1) / 19) ** 0.8
        else:
            self.max_speed_mps = 5.5

        accel_attr = attrs.get("acceleration")
        if accel_attr is not None:
            self.accel_mps2 = 2.0 + (6.0 - 2.0) * ((accel_attr - 1) / 19) ** 0.8
        else:
            self.accel_mps2 = 4.0

        self.current_speed = 0.0
        self.speed_mps = self.max_speed_mps

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
    "offside":False,
    
}
        self.flags = self.state_flags          # ← alias so p.flags[...] works
        self.code  = f"{self.rn}{self.team_code}"


        self.orientation_deg = None
    def set_target(self, xyz): self.target = tuple(xyz) if xyz else None
    def clear_target(self):     self.target = None
    def has_arrived(self):
        if not self.target: return True
        x,y,_ = self.location; xt,yt,_ = self.target
        dx,dy = xt-x, yt-y
        return (dx*dx + dy*dy) ** 0.5 <= self.arrive_radius

    def update_location(self, new_location):
        self.location = tuple(new_location)
    
    def __repr__(self):
        return f"<Player {self.sn}{self.team_code} ({self.name}) at {self.location}>"
    

