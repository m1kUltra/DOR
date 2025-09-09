# matchEngine/actions/catch.py
"""Catch action for players attempting to secure the ball."""

from typing import Optional, Tuple, Callable
import math
import random
from utils.laws import advantage as adv_law

XYZ = Tuple[float, float, float]

def do_action(
    match,
    catcher_id: str,
    subtype: Optional[str],
    location: XYZ,
    target: XYZ,
    rng: Callable[[], float] = random.random,
) -> bool:
    """
    Attempt to catch the ball.

    subtype may hint failure: e.g. "fail", "drop"
    Returns:
        True if cleanly caught (or juggled-but-secured), False otherwise.
    """
    ball = match.ball
    catcher = match.get_player_by_code(catcher_id)
    if not catcher:
        return False

    # Defensive reads of attributes
    handling = float(catcher.norm_attributes.get("handling", 0.0))
    technique = float(catcher.norm_attributes.get("technique", 0.0))

    # Use Euclidean distance in the horizontal plane
    bx, by, bz = ball.location
    cx, cy, cz = catcher.location
    
    space = math.hypot(bx - cx, bz - cz)

    # Explicit failure via subtype hint
    

    # Success probability
    if space < 1.15:
        catch_success = 0.5 + handling
        print ("near " ,catch_success)
    else:
        catch_success = 0.3 + 0.9 * (handling * technique)
        print ("far", catch_success)
    catch_success = max(0.0, min(1.0, catch_success))

    roll = rng() - .25

    # Resolve outcome
    if roll <= catch_success:
        # Clean catch
        ball.holder = catcher_id
        ball.set_action("caught")
        return True

    # Near-miss: secured after a bobble/juggle (do not mark as 'caught' if you
    # want to differentiate; here we mark 'juggled_catch' for downstream logic)
    catch_error = roll - catch_success 
    if catch_error < 0.2 :
        ball.holder = catcher_id
        ball.set_action("caught")
        # TODO: implement ball_juggle(catcher)
        return True

    # Failed catch
    # Optional: determine if it's a knock-on vs simple drop based on ball vector.
    # For now, assume knock-on goes to the other team.
    to_team = "b" if getattr(catcher, "team_code", None) == "a" else "a"
    match.advantage = adv_law.start(
        match.advantage,
        type_="knock_on",
        to=to_team,
        start_x=bx,
        start_y=by,
        start_t=match.match_time,
        reason="knock_on",
    )
    ball.set_action("dropped")
    ball.release()
   
    return False
