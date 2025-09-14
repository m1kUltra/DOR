
from __future__ import annotations

from typing import Dict, Tuple, Optional


# Mapping ``{"team_a": {9: (x, y), ...}, "team_b": {...}}`` using jersey numbers

# Mapping ``{"team_a": {1: (x, y), ...}, "team_b": {...}}`` using jersey numbers
Vec2 = Tuple[float, float]
LineoutLayout = Dict[str, Dict[int, Vec2]]



def generate_five_man_lineout_shape(
    *,
    touch_is_bottom: bool,
    attack_dir: float,
    backline_positions: Optional[Dict[str, Dict[int, Vec2]]] = None,
) -> LineoutLayout:
    """Return player locations for a basic five‑man lineout.

    Parameters
    ----------
    touch_is_bottom:
        ``True`` if the lineout is on the bottom touchline.  When ``False`` the
        layout's y‑coordinates are mirrored to represent a top‑touchline
        lineout.
    attack_dir:
        Direction of attack for ``team_a`` (+1.0 → right, −1.0 → left).
    backline_positions:
        Optional mapping of additional player locations to merge into the
        returned layout (e.g., backs in phase play).
    """

    gap = 1.5
    sign = -attack_dir

    layout: LineoutLayout = {"team_a": {}, "team_b": {}}

    a = {
        1: (gap * sign, 5.0),
        2: (0, 0.5),
        3: (gap * sign, 15.0),
        4: (gap * sign, 10.0),
        5: (gap * sign, 12.5),
        6: (gap * sign, 7.5),
        9: (3 * gap * sign, 6.0),
    }
     # team_b = defensive pack, mirrored along x and y to face team_a

    b = {

        1: (gap * -sign, 5.0),
        2: (3 * gap * -sign, 12.0),
        3: (gap * -sign, 15.0),
        4: (gap * -sign, 10.0),
        5: (gap * -sign, 12.5),
        6: (gap * -sign, 7.5),
        9: (5 * gap * -sign, 2.0),
    }

  

    layout["team_a"].update(a)
    layout["team_b"].update(b)

    if backline_positions:
        for team_key in ("team_a", "team_b"):
            extra = backline_positions.get(team_key)
            if not extra:
                continue
            if not touch_is_bottom:
                extra = {rn: (x, -y) for rn, (x, y) in extra.items()}
            layout[team_key].update(extra)

    return layout