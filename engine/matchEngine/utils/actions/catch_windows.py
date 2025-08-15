from constants import CATCH_RADIUS, CATCH_EARLY_S, CATCH_LAND_SLOP
GRAVITY = 9.81

def compute_catch_window(ball, t_now, dt):
    """
    If ball is in_air: return a window dict, else None.
    """
    if not getattr(ball, 'in_flight', False):
        return None
    x, y, z = getattr(ball, 'location', (0.0,0.0,0.0))
    vz = getattr(ball, 'velocity', (0.0,0.0,0.0))[2]
    profile = getattr(ball, 'flight_profile', {}) or {}
    ktype = profile.get('type')
    if ktype == 'grubber':
        return None  # ground pickups only

    rising = vz > 0.0 or z > 1.0
    valid_from = t_now + CATCH_EARLY_S if rising else t_now

    # naive time to ground
    t_landing = t_now
    if vz != 0 or z > 0:
        try:
            import math
            # Solve z + vz*t - 0.5*g*t^2 = 0 for t>0
            a = -0.5 * GRAVITY
            b = vz
            c = max(z, 0.0)
            disc = b*b - 4*a*c
            if disc >= 0:
                t_pos = (-b + math.sqrt(disc)) / (2*a)
                t_landing = t_now + max(t_pos, 0.0)
        except Exception:
            t_landing = t_now

    valid_to = t_landing + CATCH_LAND_SLOP
    return {
        "center": (x,y,z),
        "radius": CATCH_RADIUS,
        "valid_from": valid_from,
        "valid_to": valid_to
    }
