# matchEngine/tactics/roles.py
from typing import TypedDict, Literal

RoleKey = Literal["kicker", "captain", "caller"]

class Roles(TypedDict):
    kicker: str   # e.g. "sn.10"
    captain: str  # e.g. "sn.10"
    caller: str   # e.g. "sn.5"

# Default; teams can override per state/team as needed.
DEFAULT_ROLES: Roles = {
    "kicker":  "sn.10",
    "captain": "sn.10",
    "caller":  "sn.5",
}
