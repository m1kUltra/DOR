# utils/actions/catch_windows.py
from typing import Iterable, Optional, Tuple, Any

XYZ = Tuple[float, float, float]

def _xyz(p: Any) -> XYZ:
    if p is None: 
        return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    # Player-like object with .location
    loc = getattr(p, "location", None)
    if isinstance(loc, (list, tuple)):
        if len(loc) == 2: return (float(loc[0]), float(loc[1]), 0.0)
        if len(loc) >= 3: return (float(loc[0]), float(loc[1]), float(loc[2]))
    return (0.0, 0.0, 0.0)

def can_catch(player_or_loc: Any, ball_loc: Any, *, radius: float = 1.0, max_height: float = 1.5) -> bool:
    """
    Catch window with state gating:
      - If given a Player object, omit if off_feet / being_tackled / tackling.
      - Within `radius` in XY, and ball height <= `max_height`.
      - If given a tuple/list instead of Player, state gating is skipped.
    """
    # Optional state gating when Player-like is passed
    flags = getattr(player_or_loc, "state_flags", None)
    if isinstance(flags, dict):
        if flags.get("off_feet", False):      return False
        if flags.get("being_tackled", False): return False
        if flags.get("tackling", False):      return False
        if flags.get("in_scrum", False):    return False
        if flags.get("in_ruck", False):    return False
    px, py, _  = _xyz(player_or_loc)
    bx, by, bz = _xyz(ball_loc)

    if bz > max_height:
        return False
    dx, dy = bx - px, by - py
    return (dx * dx + dy * dy) <= (radius * radius)

def best_catcher(players: Iterable, ball_loc: Any, *,
                 radius: float = 1.0, max_height: float = 1.5,
                 team_preference: Optional[str] = None):
    """
    Return the best player to catch (nearest within radius & height),
    honoring state gating via can_catch(). If tie, prefer team_preference ('a' or 'b').
    """
    bx, by, bz = _xyz(ball_loc)
    if bz > max_height:
        return None

    best = None
    best_d2 = float("inf")
    for p in players:
        if not can_catch(p, (bx, by, bz), radius=radius, max_height=max_height):
            continue
        px, py, _ = _xyz(p)
        d2 = (px - bx) ** 2 + (py - by) ** 2

        if best is None:
            best, best_d2 = p, d2
            continue

        if d2 < best_d2:
            best, best_d2 = p, d2
            continue

        # Tie-break on team_preference
        if team_preference and abs(d2 - best_d2) <= 1e-9:
            if getattr(p, "team_code", None) == team_preference and getattr(best, "team_code", None) != team_preference:
                best, best_d2 = p, d2

    return best
