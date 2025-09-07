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


def _default_shape(attack_dir: float) -> BacklineLayout:
    """Return a simple default backline layout for both teams.

    Parameters
    ----------
    attack_dir: float
        Direction of attack for team_a (+1.0 → right, −1.0 → left).
    """
    attack_dir=-attack_dir
    a = {
        9: (1.0 * attack_dir, -1.5),   # scrum-half
        10: (7.0 * attack_dir, -1.0),  # fly-half
        12: (6.0 * attack_dir, -3.0),  # inside centre
        13: (6.5 * attack_dir, -4.5),  # outside centre
        11: (8.0 * attack_dir, -6.0),  # left wing
        14: (8.0 * attack_dir,  6.0),  # right wing
        15: (-10.0 * attack_dir, 0.0), # full-back sweeps behind
    }
    # Defensive side is mirrored both in x and y
    b = {rn: (-x, -y) for rn, (x, y) in a.items()}
    return {"team_a": a, "team_b": b}



BACKLINE_SHAPES: Dict[str, Callable[[float], BacklineLayout]] = {
    "default": _default_shape,
}


def generate_phase_play_shape(option: str, attack_dir: float) -> BacklineLayout:
    """Generate a backline shape mapping for phase play.

    Parameters
    ----------
    option: str
        Name of the desired shape option.  If unknown, ``"default"`` is used.
    attack_dir: float
        Direction of attack for ``team_a`` (+1.0 or -1.0).

    Returns
    -------
    dict
        Mapping of ``{"team_a": {...}, "team_b": {...}}`` with jersey numbers
        (9–15) as keys and ``(x, y)`` positions as values.
    """

    shape_fn = BACKLINE_SHAPES.get(option, _default_shape)
    return shape_fn(attack_dir)

