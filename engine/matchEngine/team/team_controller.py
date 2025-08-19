# matchEngine/team_controller.py
from typing import Callable, Iterable
from team.tactics import build_default

def iterate_both(match) -> Iterable:
    """Yield both teams in a stable order: A then B."""
    yield match.team_a
    yield match.team_b

def for_both(match, fn: Callable, *args, **kwargs) -> None:
    """Run a callable(team, *args, **kwargs) for A and B."""
    for team in iterate_both(match):
        fn(team, *args, **kwargs)

def team_by_code(match, code: str):
    """'a' -> team_a, 'b' -> team_b."""
    return match.team_a if code.lower() == "a" else match.team_b

def team_of_player_id(match, player_id: str):
    """Resolve '10a' / '8b' -> team."""
    code = player_id[-1].lower()
    return team_by_code(match, code)

def ensure_attack_dirs(match) -> None:
    """
    Normalize attack directions (+1 for A, -1 for B).
    Keeps the rest of the shapes intact.
    """
    match.team_a.tactics["attack_dir"] = +1.0
    match.team_b.tactics["attack_dir"] = -1.0

def set_possession(match, code: str | None) -> None:
    """Mark which team is in possession by code ('a'/'b') or clear both when None."""
    a, b = match.team_a, match.team_b
    if code is None:
        a.in_possession = False
        b.in_possession = False
        return
    code = code.lower()
    a.in_possession = (code == "a")
    b.in_possession = (code == "b")

def reset_team_tactics(team, overrides: dict | None = None) -> None:
    """Rebuild a team's tactics from defaults (useful for fixtures/season starts)."""
    team.tactics = build_default(overrides or {})
def sync_flags(match) -> None:
    """
    Keep core flags in sync every tick:
      - possession (team_a.in_possession / team_b.in_possession)
      - match.possession ('a'/'b'/None)
      - player.has_ball (if attribute exists)
    Rules:
      - If ball.holder is set → possession = holder's team.
      - If ball.holder is None → keep previous possession (ball in flight or loose).
    """
    holder_id = getattr(match.ball, "holder", None)
    prev_holder = getattr(match, "_prev_holder_id", None)

    # Fast exit if nothing changed
    if holder_id == prev_holder:
        return

    # Remember for next tick
    match._prev_holder_id = holder_id

    # Clear has_ball on everyone (if present)
    for t in (match.team_a, match.team_b):
        for p in getattr(t, "squad", []):
            if hasattr(p, "has_ball"):
                p.has_ball = False

    if holder_id:
        code = holder_id[-1].lower() if isinstance(holder_id, str) else None
        if code in ("a", "b"):
            set_possession(match, code)
            # also store a quick alias if you find it handy
            match.possession = code
        # mark carrier
        try:
            carrier = match.get_player_by_code(holder_id)
            if carrier is not None and hasattr(carrier, "has_ball"):
                carrier.has_ball = True
        except AttributeError:
            pass
    else:
        # holder None → keep existing possession; just record alias
        if getattr(match.team_a, "in_possession", False):
            match.possession = "a"
        elif getattr(match.team_b, "in_possession", False):
            match.possession = "b"
        else:
            match.possession = None