# matchEngine/team.py

class Team:
    def __init__(self, name, squad=None, tactics=None):
        self.name = name
        self.squad = squad or []  # List of Player objects
        self.tactics = tactics or {}
        self.in_possession = False

    def get_player_by_sn(self, sn):
        return next((p for p in self.squad if p.sn == sn), None)

    def get_player_by_rn(self, rn):
        return next((p for p in self.squad if p.rn == rn), None)

    def set_possession(self, value: bool):
        self.in_possession = value

    def __repr__(self):
        return f"<Team {self.name} - {len(self.squad)} players>"
