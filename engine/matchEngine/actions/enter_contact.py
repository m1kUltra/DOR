# matchEngine/actions/enter_contact.py
# actions/enter_contact.py
def perform(player, match):
    if getattr(match, "ruck_meta", None):
        return  # ruck already formed this tick; no-op
    match.ball.release()
    match.ball.location = player.location
