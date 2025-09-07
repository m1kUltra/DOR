from __future__ import annotations
from typing import Dict, Tuple, Optional

Vec2 = Tuple[float, float]
ScrumLayout = Dict[str, Dict[int, Vec2]]  # keep jersey numbers as ints


def generate_scrum_shape(
    r: float = 1.0,
    gap: float = 0.3,
    row_depth: float = 2.15,
    *,
    flanker_bind_forward: float = 0.20,
    flanker_y: float = 3.40,
    back_offset: float = 2.0,
    include_scrum_halves: bool = False,
    sh_y_offsets: Tuple[float, float] = (-4.20, -5.60),
    backline_positions: Optional[Dict[str, Dict[int, Vec2]]] = None,
    attack_dir: float = +1.0,  # +1.0 → attack to +x (right), -1.0 → attack to -x (left)
) -> ScrumLayout:
    """Create a scrum layout for both teams, oriented by attack_dir.

    attack_dir:
        +1.0 means the attacking team (team_a) plays to +x (right),
        -1.0 means the attacking team plays to -x (left).
    """

    # Base geometric quantities derived from inputs
    lateral = 2.0 * r
    front_x = (2.0 * r + gap) / 2.0
    lock_x = front_x + row_depth
    flanker_x = front_x + row_depth - flanker_bind_forward
    no8_x = lock_x + back_offset

    # If attacking to +x, the attacking pack starts on -x (faces right).
    # If attacking to -x, the attacking pack starts on +x (faces left).
    sign = -attack_dir

    layout: ScrumLayout = {"team_a": {}, "team_b": {}}

    # team_a = attacking pack, oriented by `sign`
    a = layout["team_a"]
    a.update(
        {
            1: (sign * front_x, +lateral),
            2: (sign * front_x, 0.0),
            3: (sign * front_x, -lateral),
            4: (sign * lock_x, +1.0),
            5: (sign * lock_x, -1.0),
            6: (sign * flanker_x, +flanker_y),
            7: (sign * flanker_x, -flanker_y),
            8: (sign * no8_x, 0.0),
        }
    )
    if include_scrum_halves:
        a[9] = (0.0, sh_y_offsets[0])

    # team_b = defensive pack, mirrored along x and y to face team_a
    b = layout["team_b"]
    b.update(
        {
            1: (-sign * front_x, -lateral),
            2: (-sign * front_x, 0.0),
            3: (-sign * front_x, +lateral),
            4: (-sign * lock_x, +1.0),
            5: (-sign * lock_x, -1.0),
            6: (-sign * flanker_x, +flanker_y),
            7: (-sign * flanker_x, -flanker_y),
            8: (-sign * no8_x, 0.0),
        }
    )
    if include_scrum_halves:
        b[9] = (0.0, sh_y_offsets[1])

    # Merge externally supplied backline positions
    if backline_positions:
        for team_key in ("team_a", "team_b"):
            extra = backline_positions.get(team_key)
            if extra:
                layout[team_key].update(extra)

    return layout
