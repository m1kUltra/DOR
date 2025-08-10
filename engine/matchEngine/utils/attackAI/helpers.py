# utils/attackAI/helpers.py
from math import radians, cos, sin

def forward_ray_vectors(dir_: float, deg: float):
    """Unit forward ray, flipped by attack dir (+1/-1)."""
    a = radians(deg)
    return cos(a) * dir_, sin(a) * dir_
