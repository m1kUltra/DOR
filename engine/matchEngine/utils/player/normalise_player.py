# utils/player/attr_normalize.py

from typing import Dict, Any

# One place to define all attributes you expect + their defaults
DEFAULT_ATTRS: Dict[str, float] = {
    # technical
    "darts": 4.0, "finishing": 5.0, "footwork": 9.0, "goal_kicking": 5.0,
    "handling": 6.0, "kicking": 5.0, "kicking_power": 5.0, "lineouts": 2.0,
    "marking": 20.0, "offloading": 5.0, "passing": 13.0, "scrummaging": 16.0,
    "rucking": 19.0, "technique": 9.0,

    # mental
    "aggression": 8.0, "anticipation": 9.0, "bravery": 10.0, "composure": 15.0,
    "concentration": 16.0, "decisions": 19.0, "determination": 11.0, "flair": 14.0,
    "leadership": 13.0, "off_the_ball": 10.0, "positioning": 7.0, "teamwork": 9.0,
    "vision": 16.0, "work_rate": 4.0,

    # physical
    "acceleration": 12.0, "agility": 3.0, "balance": 12.0, "jumping_reach": 5.0,
    "natural_fitness": 13.0, "pace": 11.0, "stamina": 11.0, "strength": 16.0,
}

def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0

def normalize_attrs(raw: Dict[str, Any] | None,
                    clamp_1_20: bool = True,
                    defaults: Dict[str, float] = DEFAULT_ATTRS) -> Dict[str, float]:
    """
    - Coerces all values to float
    - Fills missing keys from defaults
    - Optionally clamps to [1, 20]
    """
    raw = raw or {}
    out: Dict[str, float] = {}

    for k, default in defaults.items():
        val = _to_float(raw.get(k, default))
        if clamp_1_20:
            if val < 1.0:  val = 1.0
            if val > 20.0: val = 20.0
        out[k] = val

    # keep unknown extras (future-proof), normalized & optionally clamped
    for k, v in raw.items():
        if k in out:
            continue
        val = _to_float(v)
        if clamp_1_20:
            if val < 1.0:  val = 1.0
            if val > 20.0: val = 20.0
        out[k] = val

    return out
