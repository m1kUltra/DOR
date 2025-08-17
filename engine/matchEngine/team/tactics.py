# matchEngine/tactics/tactics.py
from typing import Dict, Any

# Single place for the defaults you had inside Team.tactics
DEFAULT_TACTICS: Dict[str, Any] = {
    # direction (+1 attack to x+, -1 attack to x-)
    "attack_dir": +1.0,

    # --- attacking shape ---
    "attack_depth_10": 7.0,
    "backline_lateral_gap": 7.0,
    "backline_min_behind": 3.0,
    "pod_gap": 6.0,
    "pod_depth": 2.0,
    "far_wing_margin": 4.0,

    # --- defense ---
    "def_line_depth": 1.0,
    "def_spacing_infield": 3.0,
    "def_pillar1_offset": (1.0, -1.0),
    "def_pillar2_offset": (1.0, +1.0),
}

def build_default(overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return a tactics dict (copy) merged with optional overrides."""
    t = dict(DEFAULT_TACTICS)
    if overrides:
        t.update(overrides)
    return t
