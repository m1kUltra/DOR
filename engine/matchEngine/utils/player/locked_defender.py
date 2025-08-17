# matchEngine/utils/locked_defender.py

def set_locked_defender(match):
    """
    Find the nearest opponent to ball.holder and mark them as the locked defender.
    - Sets state_flags["locked_defender"] = True on that defender (False for others on that team)
    - Stores match.locked_defender = "<sn><team_code>" for quick reference
    - Returns the Player object, or None if no holder / no opponent found
    """
    holder_id = getattr(match.ball, "holder", None)  # e.g. "10a"
    if not holder_id or len(holder_id) < 2:
        return None

    holder_sn = str(holder_id[:-1])
    holder_team_code = holder_id[-1]

    # teams
    atk_team = match.team_a if holder_team_code == "a" else match.team_b
    def_team = match.team_b if holder_team_code == "a" else match.team_a

    # holder player
    holder = atk_team.get_player_by_sn(holder_sn)
    if holder is None:
        # last-gasp scan if sn types differ
        for p in atk_team.squad:
            if str(p.sn) == holder_sn:
                holder = p
                break
    if holder is None or not def_team.squad:
        return None

    hx, hy, _ = holder.location

    # clear existing flags on defenders
    for d in def_team.squad:
        if hasattr(d, "state_flags"):
            d.state_flags["locked_defender"] = False

    # nearest by 2D distance
    def _d2(p):
        x, y, _ = p.location
        dx, dy = x - hx, y - hy
        return dx*dx + dy*dy

    nearest = min(def_team.squad, key=_d2)
    if hasattr(nearest, "state_flags"):
        nearest.state_flags["locked_defender"] = True

    try:
        match.locked_defender = f"{nearest.sn}{nearest.team_code}"
    except Exception:
        pass

    return nearest
 