from utils import scoring  # your existing domain scorer

def process_try_if_scored(match):
    """
    Checks try conditions; if scored, updates board and flags.
    Keeps logic centralized and testable.
    """
    if not match.ball.holder or match.period.get("status") != "live":
        return False

    holder = match.get_player_by_code(match.ball.holder)
    if not holder:
        return False

    x, y, _ = holder.location
    ev = None
    if holder.team_code == "a" and x >= 100.0:
        ev = scoring.award_try(match, "a", (x, y))
    elif holder.team_code == "b" and x <= 0.0:
        ev = scoring.award_try(match, "b", (x, y))

    if not ev:
        return False

    team = ev["team"]
    match.scoreboard[team] += ev.get("points_added", 5)
    match.pending_restart = {"type": "post_score", "to": ev["next_restart_to"]}
    match.conversion_ctx = ev.get("conversion")
    return True
