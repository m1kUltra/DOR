from typing import List, Optional
from .tactics import build_default       # ← relative import
from .roles import DEFAULT_ROLES         # ← relative import

class Team:
    def __init__(self, name: str, squad: Optional[List] = None,
                 tactics: Optional[dict] = None, roles: Optional[dict] = None):
        self.name = name
        self.squad = squad or []                     # list[Player]
        self.tactics = build_default(tactics)        # dict of flags/shapes
        self.roles = dict(roles or DEFAULT_ROLES)    # {"kicker":"sn.10", ...}
        self.in_possession = False
        self.score = 0

    def get_player_by_sn(self, sn: int):
        return next((p for p in self.squad if getattr(p, "sn", None) == sn), None)

    def get_player_by_rn(self, rn: int):
        return next((p for p in self.squad if getattr(p, "rn", None) == rn), None)

    def __repr__(self):
        return f"<Team {self.name} - {len(self.squad)} players>"

    @property
    def attack_sign(self) -> int:
        """+1 if attacking towards +x, -1 otherwise (fallback to +1)."""
        return int(self.tactics.get("attack_dir", 1))
