# matchEngine/utils/ruck_utils.py
from typing import List, Tuple
from constants import RUCK_GATE_WIDTH
# utils/ruck_utils.py
from constants import GATE_DEPTH
def compute_last_feet_line(anchor_x: float, attack_dir: float) -> float:
    return anchor_x - attack_dir * GATE_DEPTH

def is_legal_entry(player_xy: Tuple[float,float], anchor_xy: Tuple[float,float], attack_dir: float, gate_width: float = RUCK_GATE_WIDTH) -> bool:
    px, py = player_xy; ax, ay = anchor_xy
    # enter through “gate” behind anchor along attack_dir with lateral band
    return ((ax - px) * attack_dir >= -0.5) and (abs(py - ay) <= gate_width)

def nearest_n(players: List[object], ref_xy: Tuple[float,float], n: int) -> List[object]:
    ax, ay = ref_xy
    arr = sorted(players, key=lambda p: (p.rn, p.sn))
    arr.sort(key=lambda p: ( (p.location[0]-ax)**2 + (p.location[1]-ay)**2 ))
    return arr[:max(0, n)]
