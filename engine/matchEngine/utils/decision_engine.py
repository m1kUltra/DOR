# matchEngine/utils/decision_engine.py

from constants import TACKLE_RANGE

# Role Groups
FORWARDS = {1, 2, 3, 4, 5, 6, 7, 8}
BACKS = {9, 10, 11, 12, 13, 14, 15}

def process_decision(player, game_state, ball, team, opposition_team, pitch):
    """
    Core decision loop for a player.
    Returns:
        - new_action (str): e.g. "run", "pass", "kick", "support"
        - new_position (tuple): (x, y, z)
    """

    holder_code = f"{player.sn}{player.team_code}"
    is_holder = (ball.holder == holder_code)

    # Override by game state (if any custom logic per state)
    if hasattr(game_state, "override_decision"):
        override = game_state.override_decision(player, match=None)  # Match optional here
        if override:
            return override

    if is_holder:
        return decision_as_holder(player)

    if game_state.name == "ruck":
        return position_for_ruck(player, ball, team)

    if game_state.name == "open_play":
        return position_for_open_play(player, ball, team)

    if game_state.name == "restart":
        return position_for_restart(player, ball, team)

    return "idle", player.location


# ------------------------------
# Ball Holder Decision Logic
# ------------------------------

def decision_as_holder(player):
    """
    Chooses what the ball carrier will do based on rn and awareness.
    """
    awareness = player.attributes.get("mental", {}).get("awareness", 50)

    if player.rn in BACKS:
        if awareness > 70:
            return "pass", player.location
        elif awareness > 50:
            return "kick", player.location
        else:
            speed = player.attributes.get("physical", {}).get("speed", 5.0)
            run_dist = speed * 0.2
            new_x = min(player.location[0] + run_dist, 100.0)
            return "run", (new_x, player.location[1], 0.0)

    elif player.rn in FORWARDS:
        return "enter_contact", player.location

    return "hold", player.location


# ------------------------------
# Ruck Support Logic
# ------------------------------

def position_for_ruck(player, ball, team):
    x, y, _ = ball.location

    if player.rn in FORWARDS:
        spacing = (player.rn % 3) * 1.0  # 0, 1, 2m from ball
        return "support", (x - 1.0, y + spacing, 0.0)

    elif player.rn == 9:
        return "support", (x - 1.0, y, 0.0)

    elif player.rn == 10:
        return "support", (x - 5.0, y + 5.0, 0.0)

    elif player.rn == 15:
        median_x = (x + 0.0) / 2
        return "cover", (median_x, y, 0.0)

    else:
        return "line_up", (x - 10.0, y + (player.rn - 10) * 3.0, 0.0)


# ------------------------------
# Open Play Logic
# ------------------------------

def position_for_open_play(player, ball, team):
    x, y, _ = ball.location

    if player.rn == 15:
        median_x = (x + 0.0) / 2
        return "cover", (median_x, y, 0.0)

    elif player.rn in BACKS:
        offset = (player.rn - 9) * 5
        return "shape", (x - 10.0 + offset, y + 10.0, 0.0)

    elif player.rn in FORWARDS:
        return "support", (x - 5.0, y - 5.0 + player.rn, 0.0)

    return "drift", player.location


# ------------------------------
# Restart Kickoff Logic
# ------------------------------

def position_for_restart(player, ball, team):
    if player.rn == 10:
        return "kick", ball.location

    elif player.rn in FORWARDS:
        return "press", (45.0, player.sn * 2, 0.0)

    elif player.rn in BACKS:
        return "align", (30.0, player.sn * 2.5, 0.0)

    return "idle", player.location
