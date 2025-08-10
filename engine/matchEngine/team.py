# matchEngine/team.py

class Team:
    def __init__(self, name, squad=None, tactics=None):
        self.name = name
        self.squad = squad or []  # List of Player objects
        self.tactics = {
            # direction (+1 attack to x+, -1 attack to x-)
            "attack_dir": +1.0,  # team A will be set to +1, team B to -1 in setup

            # --- attacking shape ---
            "attack_depth_10": 7.0,         # fly-half pocket depth behind ball
            "backline_lateral_gap": 7.0,    # spacing between 10-12-13-14/11 across Y
            "backline_min_behind": 3.0,     # minimum onside buffer behind ball x
            "pod_gap": 6.0,                 # lateral gap between pod lanes
            "pod_depth": 2.0,               # forwards sit just behind ball
            "far_wing_margin": 4.0,         # wings stay inside touch by this many meters

            # --- defense ---
            "def_line_depth": 1.0,          # first defender depth off ball x
            "def_spacing_infield": 3.0,     # lateral spacing for backs in line
            "def_pillar1_offset": (1.0, -1.0),
            "def_pillar2_offset": (1.0, +1.0),

            # room for future: "defense_style": "drift" | "blitz", etc.
        }
        if tactics:
            self.tactics.update(tactics)

        self.in_possession = False

    def get_player_by_sn(self, sn):
        return next((p for p in self.squad if p.sn == sn), None)

    def get_player_by_rn(self, rn):
        return next((p for p in self.squad if p.rn == rn), None)

    def set_possession(self, value: bool):
        self.in_possession = value

    def __repr__(self):
        return f"<Team {self.name} - {len(self.squad)} players>"
