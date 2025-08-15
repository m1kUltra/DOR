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


"""
 handling
 if a pass travels along  inside and your catch-zone a player may attempt to catch 
 to be elgible the pass must be directed at them. on carrier.desicion_making they pick them as the receiver
 or if a defender chooses to defenderai.intercept
 a player knows the the specs of ball.pass and will attempt to be there in time to catch
 a player will turn and catch ball facing it (not passes will be aimed slighlty ahead so a good pass will not make them slow down) (within .75pi of them)

there ability to catch is determiend by 

space = |ball.x - player.x|
if space < .5
    catch_success = 0. 5 + norm(handling)-skill.modifiers
else catch_success =  0.3 + 0.9 (norm(handling)*norm(technique)
 
 if catch_success > random
    return catch

catch_error = random - catch_success

if catch_error < .2
    ball_juggle(player)

else knock-on state


ball juggle is a non-chosen game action state for the player
"""