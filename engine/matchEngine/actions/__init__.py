# matchEngine/actions/__init__.py

from actions.pass_action import do_action as do_pass
from actions.kick import do_action as do_kick
#from actions.enter_contact import do_action as do_enter_contact
from actions.catch import do_action as do_catch
from actions.movement import do_action as do_move
# We intentionally DO NOT auto-call "run" here — movement is handled by BaseState

DISPATCHABLE = {
    "pass": do_pass,
    "kick": do_kick,
    #"enter_contact": do_enter_contact,
    "catch": do_catch,
    "move": do_move
}

def dispatch(player, match):
    """
    Execute ball-affecting actions for the given player.
    NOTE:
      - No 'self' here; this is a module-level function.
      - Do not clear match flags here; states consume them after routing.
    """
    act = player.current_action
    fn = DISPATCHABLE.get(act)
    if fn is not None:
        fn(player, match)
   