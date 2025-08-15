# utils/mods.py
from math import exp

def skill_modifiers(ctx, p):
    """Return a scalar multiplier ~[0.7..1.3] composed from fatigue, pressure, temperament & weather."""
    # Pressure from context (nearest defender distance, etc.)
    pressure = ctx.get("defense_map", {}).get("pressure_on_holder", 0.0)  # 0..1
    # Hidden traits
    temperament = (p.hidden.get("Temperament", 10.0) / 20.0)  # 0..1
    professionalism = (p.hidden.get("Professionalism", 10.0) / 20.0)
    consistency = (p.hidden.get("Consistency", 10.0) / 20.0)

    # Example shaping: pressure penalty damped by temperament
    press_mult = 1.0 - 0.25 * pressure * (1.0 - temperament)

    # Fatigue placeholder (wire later): 1.0 fresh -> 0.85 tired
    fatigue_mult = ctx.get("fatigue_mult", {}).get(p, 1.0)

    # Consistency narrows variance, not mean; expose separately:
    variance_mult = 1.0 - 0.3 * (consistency - 0.5)  # ~[0.85..1.15]

    return {
        "skill": max(0.7, min(1.3, press_mult * fatigue_mult * (0.9 + 0.1*professionalism))),
        "variance": variance_mult
    }
