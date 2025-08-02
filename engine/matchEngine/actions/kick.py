# matchEngine/actions/kick.py

def perform(player, match):
    """
    Kick the ball forward 15 meters and release it.
    """
    x, y, z = player.location
    match.ball.location = (min(x + 15.0, match.pitch.length), y, 3.0)  # ball in air
    match.ball.release()
