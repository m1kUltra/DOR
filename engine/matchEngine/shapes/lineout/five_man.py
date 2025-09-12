from __future__ import annotations
from typing import Dict, Tuple
Vec2 = Tuple[float, float]
# Mapping ``{"team_a": {9: (x, y), ...}, "team_b": {...}}`` using jersey numbers

# Mapping ``{"team_a": {1: (x, y), ...}, "team_b": {...}}`` using jersey numbers
LineoutLayout = Dict[str, Dict[int, Vec2]]

def generate_five_man_lineout_shape(*, touch_is_bottom: bool, attack_dir: float) -> LineoutLayout:
   
    vert = -1.5 if touch_is_bottom else 1.5
    dvert = -vert
    attack_dir = -attack_dir

    a = {
       
       
    1: (vert * attack_dir, 5.0),
    2: (vert * attack_dir, 0.0),
    3: (vert * attack_dir, 15.0),
    4: (vert * attack_dir, 10.0),
    5: (vert * attack_dir, 12.5),
    6: (vert * attack_dir, 7.5),
     9: ((3*vert) * attack_dir, 6),
    }
     # team_b = defensive pack, mirrored along x and y to face team_a
    b = {
             1: (dvert * attack_dir, 5.0),
    2: ((vert*3) * -attack_dir, 12.0),
    3: (vert * -attack_dir, 15.0),
    4: (vert * -attack_dir, 10.0),
    5: (vert * -attack_dir, 12.5),
    6: (vert * -attack_dir, 7.5),
    9: ((vert*3) * -attack_dir, 2),

        }
    
    # Defensive side is mirrored both in x and y

    # Defensive side is mirrored in both axes

    return {"team_a": a, "team_b": b}
