from __future__ import annotations
from typing import Dict, Tuple, Optional
Vec2 = Tuple[float, float]

# Mapping ``{"team_a": {9: (x, y), ...}, "team_b": {...}}`` using jersey numbers

# Mapping ``{"team_a": {1: (x, y), ...}, "team_b": {...}}`` using jersey numbers
LineoutLayout = Dict[str, Dict[int, Vec2]]


def generate_five_man_lineout_shape(*, touch_is_bottom: bool, attack_dir: float, backline_positions: Optional[Dict[str, Dict[int, Vec2]]] = None ) -> LineoutLayout:
    
    gap = 1.5  
    layout = {"team_a": {}, "team_b": {}}
    attack_dir = -attack_dir

    a = {
       
       
    1: (gap * attack_dir, 5.0),
    2: (gap * attack_dir, 0.5),
    3: (gap * attack_dir, 15.0),
    4: (gap * attack_dir, 10.0),
    5: (gap * attack_dir, 12.5),
    6: (gap * attack_dir, 7.5),
     9: (3*gap* attack_dir, 6),
    }
     # team_b = defensive pack, mirrored along x and y to face team_a
    b = {
             1: (gap * -attack_dir, 5.0),
    2: (gap*3 * -attack_dir, 12.0),
    3: (gap * -attack_dir, 15.0),
    4: (gap * -attack_dir, 10.0),
    5: (gap * -attack_dir, 12.5),
    6: (gap * -attack_dir, 7.5),
    9: (gap*5 * -attack_dir, 2),

        }
    if backline_positions:
        for team_key in ("team_a", "team_b"):
            extra = backline_positions.get(team_key)
            if extra:
                layout[team_key].update(extra)

    return layout
    
    # Defensive side is mirrored both in x and y

    # Defensive side is mirrored in both axes

    
