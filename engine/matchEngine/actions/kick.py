# matchEngine/actions/kick.py

import math
from constants import DEFAULT_BALL_SPEED

def _attack_dir(match, team_code: str) -> float:
    team = match.team_a if team_code == 'a' else match.team_b
    return float(team.tactics.get("attack_dir", +1.0))

def perform(player, match):
    """
    Kick with simple physics, augmented by decision-layer hints:
      - initial speed scaled by player's 'kicking' attribute and v0_hint (0..1+)
      - elevation angle varies by kick_type (clearance, bomb, chip, crossfield, grubber)
      - optional lateral_hint nudges vy; fallback keeps a small bias to nearest touch
      - release ball; Ball.update() handles flight/bounce/touch
    """
    # only holder can kick
    code = f"{player.sn}{player.team_code}"
    if match.ball.holder != code:
        return

    # decision-layer metadata (optional)
    meta = getattr(player, "action_meta", {}) or {}
    ktuple = meta.get("kick_tuple")  # (kick_type, v0_hint, lateral_hint) or None

    # power from attributes (+ decision v0_hint)
    tech = player.attributes.get("technical", {})
    kicking = float(tech.get("kicking", 60))
    speed_scale = 0.6 + (kicking / 100.0) * 0.8  # 0.6 .. 1.4
    v0_hint = float(ktuple[1]) if ktuple else 1.0
    v0 = DEFAULT_BALL_SPEED * speed_scale * v0_hint  # m/s

    # direction & elevation
    dir_x = _attack_dir(match, player.team_code)
    ktype = ktuple[0] if ktuple else "generic"
    elev_map_deg = {
        "clearance": 35.0,
        "bomb":      55.0,
        "chip":      25.0,
        "crossfield":38.0,
        "grubber":   10.0,
        "generic":   35.0,
    }
    angle_el = math.radians(elev_map_deg.get(ktype, 35.0))

    # lateral component vy: use hint if provided, else small bias to touch
    _, py, _ = player.location
    if ktuple and ktuple[2] is not None:
        vy_frac = float(ktuple[2])  # expected small magnitude (e.g., 0..0.2)
    else:
        lateral_sign = +1.0 if py < 35.0 else -1.0
        vy_frac = 0.05 * lateral_sign  # default ~5% sideways

    # resolve velocity components
    vx = v0 * math.cos(angle_el) * dir_x
    vy = v0 * vy_frac
    vz = v0 * math.sin(angle_el)

    # release into flight
    match.ball.release()
    match.ball.location = (player.location[0], player.location[1], 1.5)  # off the boot
    match.ball.velocity = (vx, vy, vz)
    match.ball.in_flight = True

    # remember who kicked last (used for lineout throw-to, etc.)
    match.last_touch_team = player.team_code
