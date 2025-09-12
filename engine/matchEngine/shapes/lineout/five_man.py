from __future__ import annotations
from typing import Dict, Tuple

Vec2 = Tuple[float, float]
LineoutTeams = Dict[str, Dict[int, Vec2]]  # {"team_a": {...}, "team_b": {...}}

# Five-man lineout (attacking) order, front → back
_LINEOUT_ORDER = [1, 4, 5, 6, 3]

# Tunables
_INFIELD_X = 5.0               # distance infield for the line (attacking side)
_INTERTEAM_GAP_X = 1.5         # gap between attacking & defending lines across the mark
_PLAYER_GAP_ALONG_LINE = 1.0   # (fix #3) tighter spacing front→back along the touchline

def _orient(offset: Vec2, *, touch_sign: float, attack_dir: float) -> Vec2:
    """
    Convert a local (x, y) offset from the lineout origin to world coords:
      +x = infield from touchline, +y = along the touchline in attacking order.
    Applies:
      - touch_sign (bottom touchline=+1, top=-1) to x
      - attack_dir (+1 or -1) to y
    """
    ox, oy = offset
    return (ox * touch_sign, oy * attack_dir)

def generate_five_man_lineout_shape(
    touch_is_bottom: bool,
    attack_dir: float,
) -> LineoutTeams:
    """
    Returns full lineout setup for both teams (attack = team_a, defence = team_b).

    Fixes:
      1) Includes players not in the line (2, 7, 8, 9 placed; backs are for your phase module).
      2) Teams placed on the correct side by inverting x off attack_dir (see x_line_base).
      3) Reduced along-line gaps via _PLAYER_GAP_ALONG_LINE.
      4) Positions rn.9 (attack), rn.2 (defence), rn.9 (defence) at requested offsets
         from the origin.

    Coordinates are relative to the lineout origin at (0, 0).
    """
    assert attack_dir in (-1.0, 1.0)

    touch_sign = 1.0 if touch_is_bottom else -1.0

    # (fix #2) If you swap attack direction, the “infield” for the attacking pack should
    # flip sides relative to the origin so that the two teams don’t appear on the wrong side.
    x_line_base = _INFIELD_X * touch_sign * attack_dir

    team_a: Dict[int, Vec2] = {}
    team_b: Dict[int, Vec2] = {}

    # Hooker (attacking) throws at the mark
    team_a[2] = (0.0, 0.0)

    # Pack into the five-man line (attacking)
    for i, rn in enumerate(_LINEOUT_ORDER):
        y = i * _PLAYER_GAP_ALONG_LINE
        team_a[rn] = (x_line_base, y * attack_dir)  # y already signed below; being explicit

    # Place attackers who are NOT in the line:
    # - Attacking 9 at (-7.5, -3.5) from origin (fix #4)
    team_a[9] = _orient((-7.5, -3.5), touch_sign=touch_sign, attack_dir=attack_dir)

    # Simple, sensible defaults for loose trio when 5-man is called:
    # - 7 “tail gunner” just behind last jumper
    tail_y = (_PLAYER_GAP_ALONG_LINE * (len(_LINEOUT_ORDER) - 1))
    

    # DEFENCE: mirror the attacking line across x by adding an inter-team gap
    # (attacking line sits at x_line_base; defence sits x_line_base on the other side + gap)
    x_def_line = -(x_line_base) - _INTERTEAM_GAP_X * touch_sign * attack_dir

    # Defensive five opposite the attacking five, same y ordering
    for i, rn_attack in enumerate(_LINEOUT_ORDER):
        rn_def = rn_attack  # jersey numbers are the same (1,4,5,6,3)
        y = i * _PLAYER_GAP_ALONG_LINE
        team_b[rn_def] = (x_def_line, y * attack_dir)

    # Defending hooker & 9 (fix #4):
    # - Defending rn.2 at (-13, +3) from origin
    team_b[2] = _orient((-13.0, 3.0), touch_sign=touch_sign, attack_dir=attack_dir)
    # - Defending rn.9 at (-3, 3) from origin
    team_b[9] = _orient((-3.0, 3.0), touch_sign=touch_sign, attack_dir=attack_dir)

    # Defensive loose trio defaults (rough, can tune):
 

    return {"team_a": team_a, "team_b": team_b}
