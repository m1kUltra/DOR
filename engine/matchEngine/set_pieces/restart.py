# engine/matchEngine/set_pieces/restart.py

from typing import List, Tuple

from actions import kick
from constants import (
    PITCH_WIDTH,
    PITCH_LENGTH,
    Twenty2_A_X,
    Twenty2_B_X,
    The5_A_X,
    The5_B_X,
    DROP_OUT_MIN,
    DROP_OUT_MAX,
)
from actions import kick
XYZ = Tuple[float, float, float]
__all__ = ["kickoff"]

def _spread_y(n: int, margin: float = 5.0) -> List[float]:
    """Evenly spaced Y slots across the pitch with a small touchline margin."""
    if n <= 1:
        return [PITCH_WIDTH * 0.5]
    span = max(PITCH_WIDTH - 2.0 * margin, 1.0)
    step = span / float(n - 1)
    return [margin + i * step for i in range(n)]

def _rng(match):
    """Prefer the match's deterministic RNG; fallback to Python random."""
    r = getattr(match, "rng", None)
    if r and all(hasattr(r, m) for m in ("uniform", "random")):
        return r
    import random
    return random

def _player_code(sn: int, team_code: str) -> str:
    return f"{int(sn)}{team_code}"

def _sn_from_roles(team) -> int:
    """Parse roles['kicker'] like 'sn.10'; fallback to 10."""
    role = (getattr(team, "roles", None) or {}).get("kicker", "sn.10")
    try:
        return int(str(role).split(".")[-1])
    except Exception:
        return 10
    
def _drop_out(match, to: str, spot_a: float, spot_b: float) -> bool:
    """Generic helper for drop-out restarts."""
    to = (to or "b").lower()
    recv_team = match.team_a if to == "a" else match.team_b
    kick_team = match.team_b if recv_team is match.team_a else match.team_a

    recv_code = "a" if recv_team is match.team_a else "b"
    kick_code = "b" if recv_team is match.team_a else "a"

    attack_dir = float(kick_team.tactics.get("attack_dir", +1.0))

    KX = spot_a if attack_dir > 0 else spot_b
    KY = PITCH_WIDTH * 0.5

    r = _rng(match)

    yslots_k = _spread_y(len(kick_team.squad))
    for i, p in enumerate(kick_team.squad):
        back = r.uniform(1.0, 5.0)
        jitter_y = r.uniform(-2.0, 2.0)
        x = KX - attack_dir * back
        y = yslots_k[i] + jitter_y
        p.update_location(match.pitch.clamp_position((x, y, 0.0)))

    yslots_r = _spread_y(len(recv_team.squad))
    for i, p in enumerate(recv_team.squad):
        depth = r.uniform(10.0, 25.0)
        jitter_x = r.uniform(-3.0, 3.0)
        jitter_y = r.uniform(-10.0, 10.0)
        x = KX + attack_dir * depth + jitter_x
        y = yslots_r[i] + jitter_y
        p.update_location(match.pitch.clamp_position((x, y, 0.0)))

    kicker_sn = _sn_from_roles(kick_team)
    kicker = kick_team.get_player_by_sn(kicker_sn) or (
        kick_team.get_player_by_rn(10) or kick_team.squad[0]
    )
    kicker_id = _player_code(kicker.sn, kick_code)

    kicker.update_location(
        match.pitch.clamp_position((KX - attack_dir * 0.5, KY, 0.0))
    )

    match.ball.holder = kicker_id
    match.ball.location = kicker.location

    target_x = KX + attack_dir * r.uniform(DROP_OUT_MIN, DROP_OUT_MAX)
    target_x = KX + attack_dir * 10     # 10 m forward from the drop-out spot
    target_y = PITCH_WIDTH +25             # 70.0 → top touchline (use 0.0 for bottom)
    target: XYZ = (target_x, target_y, 0.0)

    kick.do_action(match, kicker_id, "dropout", match.ball.location, target)
    return True


def kickoff(match, to: str = "b") -> bool:
    """
    Hard-setup a kickoff:
      - Kicking team = opposite of `to`
      - Place kickers behind halfway; receivers scattered ahead of halfway
      - Give ball to team's 'kicker' (roles) and immediately kick with subtype 'kickoff'
    """
    to = (to or "b").lower()
    recv_team = match.team_a if to == "a" else match.team_b
    kick_team = match.team_b if recv_team is match.team_a else match.team_a

    recv_code = "a" if recv_team is match.team_a else "b"
    kick_code = "b" if recv_team is match.team_a else "a"

    # attack_dir from tactics (already set in setup.py)
    attack_dir = float((getattr(kick_team, "tactics", {}) or {}).get("attack_dir", +1.0))

    # Kick spot = halfway on X, centered Y
    KX = 50.0
    KY = PITCH_WIDTH * 0.5

    r = _rng(match)

    # --- place kicking team (behind halfway) ---
    yslots_k = _spread_y(len(kick_team.squad))
    for i, p in enumerate(kick_team.squad):
        back = r.uniform(1.0, 5.0)              # 1–5m behind halfway
        jitter_y = r.uniform(-2.0, 2.0)
        x = KX - attack_dir * back
        y = yslots_k[i] + jitter_y
        p.update_location(match.pitch.clamp_position((x, y, 0.0)))

    # --- place receiving team (ahead of halfway), scattered ±10m ---
    yslots_r = _spread_y(len(recv_team.squad))
    for i, p in enumerate(recv_team.squad):
        depth = r.uniform(10.0, 25.0)           # 10–25m ahead of halfway
        jitter_x = r.uniform(-3.0, 3.0)
        jitter_y = r.uniform(-10.0, 10.0)       # ±10 as requested
        x = KX + attack_dir * depth + jitter_x
        y = yslots_r[i] + jitter_y
        p.update_location(match.pitch.clamp_position((x, y, 0.0)))

    # --- select kicker by roles ---
    kicker_sn = _sn_from_roles(kick_team)
    kicker = (kick_team.get_player_by_sn(kicker_sn)
              or kick_team.get_player_by_rn(10)
              or kick_team.squad[0])
    kicker_id = _player_code(kicker.sn, kick_code)

    # Place kicker exactly on the kick mark
    kicker.update_location(match.pitch.clamp_position((KX - attack_dir * 0.5, KY, 0.0)))

    # --- hand ball to kicker ---
    match.ball.holder = kicker_id
    match.ball.location = kicker.location

    # --- fire the kickoff punt immediately ---
    # Aim deep into receiving half, center-ish Y
    """
    target_x = PITCH_LENGTH - 1.0 if attack_dir > 0 else 1.0
    target_y = KY + r.uniform(-8.0, 8.0)
    target: XYZ = (target_x, target_y, 0.0)
    """
    target_x = KX + attack_dir * 10     # 10 m forward from the drop-out spot
    target_y = PITCH_WIDTH +25             # 70.0 → top touchline (use 0.0 for bottom)
    target: XYZ = (target_x, target_y, 0)

    # Use the existing kick action; subtype 'kickoff' so your profiles can special-case if needed
    kick.do_action(match, kicker_id, "kickoff", match.ball.location, target)
    return True
def drop_22(match, to: str = "b") -> bool:
    """22m drop-out restart."""
    return _drop_out(match, to, Twenty2_A_X, Twenty2_B_X)


def goal_line_drop(match, to: str = "b") -> bool:
    """Goal-line drop-out restart."""
    return _drop_out(match, to, The5_A_X, The5_B_X)