# matchEngine/actions/enter_contact.py
# actions/enter_contact.py
def perform(player, match):
    if getattr(match, "ruck_meta", None):
        return  # ruck already formed this tick; no-op
    match.ball.release()
    match.ball.location = player.location

    """
     safe option disbales ability to pass or offload until a tackled is over player taget location is the 
     opposing tryline and if Target_location -2  is
     reached they will try to score
    
     
    """
