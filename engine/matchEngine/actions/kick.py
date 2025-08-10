# matchEngine/actions/kick.py

import math
from constants import DEFAULT_BALL_SPEED

def _attack_dir(match, team_code: str) -> float:
    team = match.team_a if team_code == 'a' else match.team_b
    return float(team.tactics.get("attack_dir", +1.0))

def perform(player, match):
    """
    Kick with simple physics:
      - set initial velocity from player's kicking attribute
      - 35° elevation, slight lateral bias to touch if near edge
      - release ball; Ball.update() handles flight/bounce/touch
    """
    # only holder can kick
    code = f"{player.sn}{player.team_code}"
    if match.ball.holder != code:
        return

    # power from attributes
    tech = player.attributes.get("technical", {})
    kicking = float(tech.get("kicking", 60))
    speed_scale = 0.6 + (kicking / 100.0) * 0.8  # 0.6 .. 1.4
    v0 = DEFAULT_BALL_SPEED * speed_scale  # m/s

    # direction
    dir_x = _attack_dir(match, player.team_code)
    angle_el = math.radians(35.0)  # elevation
    # small lateral aim: if on left half, bias to right touch for clearance (team A),
    # keep it tiny so we don't always go out
    _, py, _ = player.location
    lateral_sign = +1.0 if py < 35.0 else -1.0
    vy_frac = 0.05 * lateral_sign  # 5% sideways; tweak later by tactics

    vx = v0 * math.cos(angle_el) * dir_x
    vy = v0 * vy_frac
    vz = v0 * math.sin(angle_el)

    # release into flight
    match.ball.release()
    match.ball.location = (player.location[0], player.location[1], 1.5)  # off boot
    match.ball.velocity = (vx, vy, vz)
    match.ball.in_flight = True

    # remember who kicked last (used for lineout throw-to)
    match.last_touch_team = player.team_code
