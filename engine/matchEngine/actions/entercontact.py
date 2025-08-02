# matchEngine/actions/enter_contact.py

def perform(player, match):
    """
    For now, assume every contact results in a ruck and ball is recycled.
    You could later add contest logic or turnovers here.
    """
    match.ball.release()  # drop the ball into ruck
    match.ball.location = player.location  # ball ends where tackled
