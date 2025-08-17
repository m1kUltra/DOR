# matchEngine/team_controller.py
from typing import Callable, Iterable
from tactics import build_default

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
