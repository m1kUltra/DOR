# matchEngine/set_pieces/place_kick.py
from typing import Optional, Tuple
from constants import PITCH_WIDTH, PITCH_LENGTH, TRYLINE_A_X, TRYLINE_B_X 
from actions import kick
from set_pieces.restart import _spread_y, _rng  # reuse helpers
import event


XYZ = Tuple[float, float, float]

def _player_code(sn: int, team_code: str) -> str:
    return f"{int(sn)}{team_code}"

def _sn_from_roles(team) -> int:
    role = (getattr(team, "roles", None) or {}).get("kicker", "sn.10")
    try:
        return int(str(role).split(".")[-1])
    except Exception:
        return 10

def _attack_dir_sign(team) -> int:
    try:
        return 1 if float((getattr(team, "tactics", {}) or {}).get("attack_dir", +1.0)) >= 0 else -1
    except Exception:
        return 1

def _clamp_xy(match, x: float, y: float) -> XYZ:
    x = max(0.5, min(PITCH_LENGTH - 0.5, float(x)))
    y = max(1.0,  min(PITCH_WIDTH  - 1.0, float(y)))
    return (x, y, 0.0)

def _own_try_x(team) -> float:
    sign = float(getattr(team, "tactics", {}).get("attack_dir", +1.0))
    return (TRYLINE_A_X + 0.5) if sign > 0 else (TRYLINE_B_X - 0.5)

def _stage_next_restart(match, receiving_code: str, exclude_ids: set[str] | None = None) -> None:
    exclude_ids = exclude_ids or set()
    recv_team = match.team_a if receiving_code == "a" else match.team_b
    kick_team = match.team_b if receiving_code == "a" else match.team_a

    r = _rng(match)
    attack_dir = float(getattr(kick_team, "tactics", {}).get("attack_dir", +1.0))

    # receivers ahead of halfway
    ys_r = _spread_y(len(recv_team.squad))
    for i, p in enumerate(recv_team.squad):
        pid = f"{int(getattr(p, 'sn', i+1))}{receiving_code}"
        if pid in exclude_ids: continue
        depth = r.uniform(10.0, 25.0)
        jitter_x = r.uniform(-3.0, 3.0)
        jitter_y = r.uniform(-10.0, 10.0)
        x = 50.0 + attack_dir * depth + jitter_x
        y = ys_r[i] + jitter_y
        p.update_location(match.pitch.clamp_position((x, y, 0.0)))

    # conceding under posts
    ys_k = _spread_y(len(kick_team.squad))
    line_x = _own_try_x(kick_team)
    kick_code = "b" if receiving_code == "a" else "a"
    for i, p in enumerate(kick_team.squad):
        pid = f"{int(getattr(p, 'sn', i+1))}{kick_code}"
        if pid in exclude_ids: continue
        jitter_y = r.uniform(-2.0, 2.0)
        p.update_location(match.pitch.clamp_position((line_x, ys_k[i] + jitter_y, 0.0)))

def conversion(
    match,
    team_code: Optional[str] = None,
    spot_y: Optional[float] = None,
    *,
    kick_subtype: Optional[str] = None,
) -> bool:
    # resolve scoring team
    if team_code not in ("a", "b"):
        tc = getattr(match, "last_try_team", None)
        if tc in ("a", "b"): team_code = tc
        else:
            hid = (getattr(match.ball, "holder", "") or "").lower()
            if hid and hid[-1] in ("a","b"): team_code = hid[-1]
            elif getattr(match, "possession", None) in ("a","b"): team_code = match.possession
            elif getattr(match.team_a, "in_possession", False): team_code = "a"
            elif getattr(match.team_b, "in_possession", False): team_code = "b"
            else: return False

    conv_team = match.team_a if team_code == "a" else match.team_b
    attack_dir = float(conv_team.tactics.get("attack_dir", +1.0))

    # tee (KX,KY)
    if spot_y is None:
        if hasattr(match, "last_try_spot"): spot_y = float(match.last_try_spot[1])
        else: _, spot_y, _ = match.ball.location
    KY = float(spot_y)
    try_x = float(TRYLINE_B_X if attack_dir > 0 else TRYLINE_A_X)
    back  = 15.0 + 0.5 * abs(KY - (PITCH_WIDTH * 0.5))
    KX    = try_x - (1 if attack_dir > 0 else -1) * back
    tee   = match.pitch.clamp_position(_clamp_xy(match, KX, KY))

    # --- FIXED: select kicker & build kicker_id correctly ---
    kicker_sn = _sn_from_roles(conv_team)
    kicker = (conv_team.get_player_by_sn(kicker_sn)
              or conv_team.get_player_by_rn(10)
              or (conv_team.squad[0] if conv_team.squad else None))
    if not kicker:
        return False
    kicker_sn_actual = int(getattr(kicker, "sn", kicker_sn))
    kicker_id = _player_code(kicker_sn_actual, team_code)  # e.g. "10a"

    # place kicker, give ball, kick
    kicker.update_location(match.pitch.clamp_position((KX - attack_dir * 0.5, KY, 0.0)))
    match.ball.holder = kicker_id
    match.ball.location = kicker.location

    target_x = (try_x + 1.0) if attack_dir > 0 else (try_x - 1.0)
    target: XYZ = (float(target_x), 35, 15)
    subtype = "conversion"
    kick.do_action(match, kicker_id, subtype, match.ball.location, target)

    # stage next restart, but DON'T move the conversion kicker
    _stage_next_restart(match, receiving_code=team_code, exclude_ids={kicker_id})
    




    # prime the restart event (scoring team receives next)
 
    return True

from utils.actions.scoring_check import conversion_checker
def conversion_transit(match,success)->bool:
    x, y, z = match.ball.location
    if False:
        conversion_checker(match)
    print(z)
    if z>0.1:
        match.ball.set_action= ("idle")
        #add scoring logic later
    return success