# matchEngine/actions/pass_action.py

import random
from constants import EPS
from utils.logger import log_tick  # optional for debug

def _team_attack_dir(match, team_code: str) -> float:
    team = match.team_a if team_code == 'a' else match.team_b
    return float(team.tactics.get("attack_dir", +1.0))

def _is_backward_pass(pass_dir: float, dx: float) -> bool:
    """
    Rugby union: pass must be lateral or backwards relative to the passer's motion/attack direction.
    Here we approximate: along X only vs team attack_dir.
    pass_dir = +1.0 if team attacks to x+, -1.0 if to x-.
    dx = recipient_x - passer_x.
    """
    # Backwards if moving opposite to attack dir, or ~0 within EPS
    if pass_dir > 0:
        return dx <= EPS
    else:
        return dx >= -EPS

def perform(player, match):
    """
    Choose a recipient on same team, ensure pass is not forward relative to attack direction.
    Add simple catch error; illegal forward or knock-on routes to ScrumState for opposition.
    """
    # Only the holder can pass
    holder_code = f"{player.sn}{player.team_code}"
    if match.ball.holder != holder_code:
        return

    team = match.team_a if player.team_code == 'a' else match.team_b
    mates = [p for p in match.players if p.team_code == player.team_code and p is not player]

    px, py, _ = player.location
    attack_dir = _team_attack_dir(match, player.team_code)

    # pick nearest *eligible* recipient (lateral/back only)
    # (you can add smarter target selection later)
    best = None
    best_d2 = None
    for m in mates:
        mx, my, _ = m.location
        dx = mx - px
        if not _is_backward_pass(attack_dir, dx):
            continue  # forward: illegal
        d2 = (mx - px) ** 2 + (my - py) ** 2
        if d2 <= (12.0 ** 2):  # within 12m
            if best is None or d2 < best_d2:
                best, best_d2 = m, d2

    if not best:
        # No legal target: drop to contact/knock-on if it goes forward, else loose ball behind
        # Here we just release ball at passer feet (slightly behind), and let tackle/ruck logic pick it up.
        behind = -0.5 if attack_dir > 0 else +0.5
        match.ball.release()
        match.ball.location = (px + behind, py, 0.0)
        match.last_touch_team = player.team_code
        # mark scrum if it effectively went forward from passer's hands
        # (when we had no legal backward option, treat this as handling error; opposition put-in)
        match.pending_scrum = {
            "x": px,
            "y": py,
            "put_in": 'b' if player.team_code == 'a' else 'a'
        }
        return

    # Simple catch success (use attributes if present)
    passer_skill = player.attributes.get('technical', {}).get('passing', 60)
    catcher_skill = best.attributes.get('technical', {}).get('catching', 60)
    pressure = 0  # you can estimate nearby defenders later
    base_success = 0.85 + (0.001 * (passer_skill + catcher_skill)) - (0.02 * pressure)
    success = random.random() < max(0.1, min(0.98, base_success))

    if success:
        match.ball.holder = f"{best.sn}{best.team_code}"
        match.ball.location = best.location
        match.last_touch_team = player.team_code
        return

    # Drop / knock-on
    # If drop propels ball forward relative to attack_dir ⇒ knock-on ⇒ scrum to opposition
    mx, my, _ = best.location
    dx = mx - px
    forward = not _is_backward_pass(attack_dir, dx)  # if intended target was forward
    match.ball.release()
    # simulate slight bobble forward if forward, otherwise behind
    bobble = +0.5 if (attack_dir > 0 and forward) else (-0.5 if attack_dir > 0 else +0.5)
    match.ball.location = (px + bobble, py, 0.0)
    match.last_touch_team = player.team_code
    if forward:
        match.pending_scrum = {
            "x": px,
            "y": py,
            "put_in": 'b' if player.team_code == 'a' else 'a'
        }
