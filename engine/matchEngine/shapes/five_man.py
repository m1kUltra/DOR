from __future__ import annotations
from typing import Dict, Tuple

"""Template lineout shape for a five-man attacking lineout.

The returned layout uses a local coordinate system with ``+x`` pointing
infield from the touch line and ``+y`` running toward the top touchline.
Positions are supplied for both the attacking side (``team_a``) and the
defensive side (``team_b``), the latter mirrored around the line with a
1.5m gap.
"""

Vec2 = Tuple[float, float]
LineoutLayout = Dict[str, Dict[int, Vec2]]

_LINEOUT_ORDER = [1, 4, 5, 6, 3]
_FRONT_X = 5.0
_BACK_X = 15.0
_DEF_GAP_X = 1.5


def generate_five_man_lineout_shape() -> LineoutLayout:
    step = (_BACK_X - _FRONT_X) / 4.0
    layout: LineoutLayout = {"team_a": {}, "team_b": {}}
    attack = layout["team_a"]
    attack[2] = (0.0, 0.0)
    for i, rn in enumerate(_LINEOUT_ORDER):
        attack[rn] = (_FRONT_X + i * step, 0.0)

    defend = layout["team_b"]
    for i, rn in enumerate(_LINEOUT_ORDER):
        x = _FRONT_X + i * step + _DEF_GAP_X
        defend[rn] = (-x, 0.0)
    return layout