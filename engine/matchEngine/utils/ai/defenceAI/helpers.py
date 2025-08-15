# utils/defenceAI/helpers.py
from typing import Tuple

def clamp_y(y: float, low: float, high: float) -> float:
    return max(low, min(high, y))
