
from typing import Callable, Dict, Tuple

Vec2 = Tuple[float, float]
# Mapping ``{"team_a": {9: (x, y), ...}, "team_b": {...}}`` using jersey numbers
BacklineLayout = Dict[str, Dict[int, Vec2]]


def default_shape(attack_dir: float) -> BacklineLayout:
    """Return a simple default backline layout for both teams.

    Parameters
    ----------
    attack_dir: float
        Direction of attack for team_a (+1.0 → right, −1.0 → left).
    """
    attack_dir=-attack_dir
    a = {
        7: (10.0 * attack_dir, 35.5),   # scrum-half
        8: (10.0 * attack_dir, 32.5),   # scrum-half
        10: (10.0 * attack_dir, 25.0),  # fly-half
        12: (10.0 * attack_dir, 43.0),  # inside centre
        13: (10.5 * attack_dir, 55.5),  # outside centre
        11: (20.0 * attack_dir, 25.0),  # left wing
        14: (10.0 * attack_dir,  65.0),  # right wing
        15: (10.0 * attack_dir, 60.0), # full-back sweeps behind
    }
    # Defensive side is mirrored both in x and y
    b = {rn: (-x, -y) for rn, (x, y) in a.items()}
    return {"team_a": a, "team_b": b}



BACKLINE_SHAPES: Dict[str, Callable[[float], BacklineLayout]] = {
    "default": default_shape,
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

    shape_fn = BACKLINE_SHAPES.get(option, default_shape)
    return shape_fn(attack_dir)