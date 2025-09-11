from __future__ import annotations
from typing import Dict, Tuple

"""Template lineout shape for a five-man attacking lineout.

The returned layout uses a local coordinate system with ``+x`` pointing
infield from the touch line and ``+y`` running toward the top touchline.
Positions are supplied for both the attacking side (``team_a``) and the
defensive side (``team_b``), the latter mirrored around the line with a
1.5m gap.
Only the attacking side's positions are generated; callers can mirror the
layout for the defence if required.
"""



Vec2 = Tuple[float, float]

# Mapping of jersey number to ``(x, y)`` coordinates for the attacking side
LineoutLayout = Dict[int, Vec2]

_LINEOUT_ORDER = [1, 4, 5, 6, 3]

_INFIELD_X = 5.0
_GAP_Y = 2.5



def generate_five_man_lineout_shape(
    touch_is_bottom: bool, attack_dir: float
) -> LineoutLayout:
    """Return an attacking five‑man lineout layout.
    Parameters
    ----------
    touch_is_bottom:
        ``True`` if the lineout is on the bottom touchline, ``False`` if on the top.
    attack_dir:
        Direction along the touchline for front-to-back ordering (+1.0 or -1.0).

    Returns
    -------
    dict
        Mapping of jersey numbers to ``(x, y)`` positions.
    """

    touch_sign = 1.0 if touch_is_bottom else -1.0
    x = _INFIELD_X * touch_sign

    layout: LineoutLayout = {2: (0.0, 0.0)}
    for i, rn in enumerate(_LINEOUT_ORDER):
      
        y = i * _GAP_Y * attack_dir
        layout[rn] = (x, y)

    return layout