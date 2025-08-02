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
