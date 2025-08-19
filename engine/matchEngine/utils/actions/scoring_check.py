def _attack_dir_for_team(match, team_code: str) -> float:
    team = match.team_a if team_code == "a" else match.team_b
    return float((getattr(team, "tactics", {}) or {}).get("attack_dir", +1.0))

def _is_over_correct_tryline(x: float, atk_dir: float) -> bool:
    return (x >= TRYLINE_B_X) if atk_dir > 0 else (x <= TRYLINE_A_X)


def check_try(match) -> bool:
    # prevent duplicate conversion events for the same try
    if getattr(match, "_pending_conversion", False):
        return True

    ball = match.ball
    hid = getattr(ball, "holder", None)
    if not hid: return False
    holder = match.get_player_by_code(hid)
    if not holder: return False

    bx, by, _ = getattr(ball, "location", holder.location)
    team_code = holder.team_code
    atk_dir   = _attack_dir_for_team(match, team_code)

    if not _is_over_correct_tryline(float(bx), atk_dir):
        return False

