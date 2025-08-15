# matchEngine/actions/run.py

def perform(player, match):
    """
    Basic run logic: move player forward (along X).
    This is simplistic for now, without collision or defenders.
    """
    x, y, z = player.location
    run_distance = 2.0  # meters per tick
    new_x = min(x + run_distance, match.pitch.length)
    player.update_location((new_x, y, z))
"""acceleration attr determines is acceleration (accel_mps2 = 2.0 + (6.0 - 2.0) * ((accel_attr - 1) / 19) ** 0.8)
pace detemrines the max speed a player can reach (5 + 5*((Pace-1)/19)^0.8)
work_rate detrmines the proportion of actual pace used by players (when they do not have the ball or the locked defender) //later
this is a sliding scale that impacts diffrent areas based on formulas 
        genral play - nothing important getting into positioon etc 
        support - involved in the surrounding play
        acytive - has the ball or their locked tackler 
turning - introduce orientation to a player in degress 90
agil_norm = (agility_attr - 1) / 19.0

    # --- Step 2: Map to lateral acceleration capability (m/s²) ---
    #   Low agility = 3 m/s²; high agility = 8 m/s²
    a_lat_max = 3.0 + (8.0 - 3.0) * agil_norm

    # --- Step 3: Convert lateral acceleration to max turn rate ---
    #   Formula: omega = a_lat / v   (v floored to avoid infinite spin)
    v_eff = max(speed_mps, 1.5)  # 1.5 m/s floor for low-speed turning
    omega_max = a_lat_max / v_eff

    # --- Step 4: Cap at a max "pivot spin" when almost stopped ---
    omega_snap_cap = 6.0  # rad/s (~343°/s)
    omega_max = min(omega_max, omega_snap_cap)
need to implment orientation
"""