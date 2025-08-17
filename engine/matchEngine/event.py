# matchEngine/events.py

"""
Events: minimal whistle-layer.
- Maintains a new_event tuple: (type, location, team)
- Called by state_controller; everything else (ball/controller) stays separate.
"""

from typing import Optional, Tuple, Any

# global current event tuple
new_event: Optional[Tuple[str, tuple[float, float], Any]] = None


def set_event(event_type: str,
              location: tuple[float, float],
              team: Any) -> None:
    """
    Create/overwrite the global new_event tuple.

    Args:
        event_type: str, e.g. "penalty_given", "scrum_given",
                    "lineout_given", "ball_dead", "try_given"
        location: (x, y) tuple on pitch
        team: team object or team code receiving the restart
    """
    global new_event
    new_event = (event_type, location, team)


def get_event() -> Optional[Tuple[str, tuple[float, float], Any]]:
    """Return the current new_event (None if none set)."""
    return new_event


def clear_event() -> None:
    """Reset event to None (after controller has handled it)."""
    global new_event
    new_event = None






""""""
"""event occured overwrites and changes states regardless of ball_status
has the role of being the refarees whistle to send us to the next state

 penalty_given fk_given, scrum_given, penalty_try_given, 
Ball determines lineout already, ball_dead, grounded_in_goal , held_up, try given 

penalty_given is a shell that then runs set_piece choices and receives there pick of what to do that will change the next state,
either something for nudeges or scrum

event.py
should have the following 
for each event if statements that determine when they are called  update the new_event tuple

then a controller function that checks if these have happened and update state.status  
to note this is onl for events but noth state.status and ball.status will influence state.status if they themselves have a new action


new_event = (type, location, team) #team is the one who will receive the ball
basically it should read advantage.py 
and convert if pen_adavanatge = no_advanatge
    new_event=(penalty, advanatge_loaction, team)
elif scrum_advantage = no_adavantage
    new_event=(penalty, advanatge_loaction, team)
##add penlat_try andfree_kicks later


"""
