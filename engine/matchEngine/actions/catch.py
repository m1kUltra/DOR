# matchEngine/actions/catch.py

def perform(player, match):
    """
    Catch a loose ball if player is near it.
    """
    if not match.ball.is_held():
        px, py, _ = player.location
        bx, by, _ = match.ball.location
        if abs(px - bx) <= 2 and abs(py - by) <= 2:
            match.ball.holder = f"{player.sn}{player.team_code}"
