from __future__ import annotations

"""Utility functions for generating backline shapes during phase play.

This module exposes :func:`generate_phase_play_shape` which returns default
backline positions for jerseys 9–15.  Shapes are expressed in a local coordinate
system centred on the breakdown/set‑piece where ``+x`` represents the attacking
team's direction of play.  ``team_a`` is treated as the attacking side in the
returned mapping while ``team_b`` is the mirror defensive side.

Future backline options can be added by defining a new shape function and
registering it in :data:`BACKLINE_SHAPES`.
"""

from typing import Callable, Dict, Tuple

Vec2 = Tuple[float, float]
# Mapping ``{"team_a": {9: (x, y), ...}, "team_b": {...}}`` using jersey numbers
BacklineLayout = Dict[str, Dict[int, Vec2]]


def generate_five_man_lineout_shape(attack_dir: float) -> BacklineLayout:
    """Return a simple default backline layout for both teams.

    Parameters
    ----------
    attack_dir: float
        Direction of attack for team_a (+1.0 → right, −1.0 → left).
    """
    attack_dir=-attack_dir
    a = {
        1: (5 * attack_dir, -1.5),   # TODO replace with tactic based pics
        3: (7.5 * attack_dir, -1.5),  
        4: (10 * attack_dir, -1.5),  
        5: (12.5 * attack_dir, -1.5),  
        6: (15 * attack_dir, -1.5),  
       
    }
    # Defensive side is mirrored both in x and y
    b = {rn: (-x, -y) for rn, (x, y) in a.items()}
    return {"team_a": a, "team_b": b}









