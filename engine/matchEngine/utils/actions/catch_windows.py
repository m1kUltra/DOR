#/utils/actions/catch_windows.py
from typing import Iterable, Optional, Tuple

XYZ = Tuple[float, float, float]

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def can_catch(player_loc: XYZ, ball_loc: XYZ, *, radius: float = 1.0, max_height: float = 1.5) -> bool:
    """
    Simple catch window:
      - within `radius` meters in the XY plane
      - ball's height <= `max_height`
    """
    px, py, _   = _xyz(player_loc)
    bx, by, bz  = _xyz(ball_loc)
    if bz > max_height:
        return False
    dx, dy = bx - px, by - py
    return (dx*dx + dy*dy) <= (radius * radius)

def best_catcher(players: Iterable, ball_loc: XYZ, *,
                 radius: float = 1.0, max_height: float = 1.5,
                 team_preference: Optional[str] = None):
    """
    Return the best player to catch (nearest within radius & height).
    If team_preference is provided ('a' or 'b'), prefer that team on ties.
    """
    bx, by, bz = _xyz(ball_loc)
    if bz > max_height:
        return None

    best = None
    best_d2 = radius * radius
    for p in players:
        px, py, _ = _xyz(getattr(p, "location", None))
        d2 = (px - bx)**2 + (py - by)**2
        if d2 <= best_d2:
            if (best is not None and team_preference and
                getattr(p, "team_code", None) != team_preference and
                getattr(best, "team_code", None) == team_preference):
                continue
            best = p
            best_d2 = d2
    return best
