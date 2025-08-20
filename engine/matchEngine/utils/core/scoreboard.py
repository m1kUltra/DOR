def score_update(match, holder, way: str):
    # Choose the team from the match, not by importing Team
    team_code = holder[-1]
    team_obj = match.team_a if team_code == "a" else match.team_b

    # Map event → points
    points_by_way = {
        "try": 5,
        "conversion": 2,
        "penalty": 3,
        "penalty_try": 7,
    }

    try:
        team_obj.score += points_by_way[way]
    except KeyError:
        raise ValueError(f"Unknown scoring type: {way!r}")

    update_scoreboard(match)


def update_scoreboard(match):
    match.scoreboard = {
        "a": match.team_a.score,
        "b": match.team_b.score,
    }
   
