# matchEngine/team.py
# matchEngine/team.py
from typing import List, Optional
from matchEngine.team import build_default, DEFAULT_ROLES

class Team:
    def __init__(self, name: str, squad: Optional[List] = None,
                 tactics: Optional[dict] = None, roles: Optional[dict] = None):
        self.name = name
        self.squad = squad or []              # list[Player]
        self.tactics = build_default(tactics) # dict of flags/shapes
        self.roles = dict(roles or DEFAULT_ROLES)  # {"kicker":"sn.10", ...}
        self.in_possession = False

    def get_player_by_sn(self, sn: int):
        return next((p for p in self.squad if getattr(p, "sn", None) == sn), None)

    def get_player_by_rn(self, rn: int):
        return next((p for p in self.squad if getattr(p, "rn", None) == rn), None)

    def __repr__(self):
        return f"<Team {self.name} - {len(self.squad)} players>"


