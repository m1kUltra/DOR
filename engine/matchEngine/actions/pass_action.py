# matchEngine/actions/pass_action.py

def perform(player, match):
    """
    Pass to the nearest player on the same team within 10 meters.
    """
    teammates = [p for p in match.players if p.team_code == player.team_code and p != player]

    x, y, z = player.location
    for mate in sorted(teammates, key=lambda m: abs(m.location[0] - x)):
        if abs(mate.location[0] - x) <= 10.0:
            match.ball.holder = f"{mate.sn}{mate.team_code}"
            return

    # No one nearby, drop ball
    match.ball.release()
