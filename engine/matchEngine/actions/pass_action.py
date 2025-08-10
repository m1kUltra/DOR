# matchEngine/actions/pass_action.py

from constants import EPS
from utils.logger import log_law  # law telemetry

def _team_attack_dir(match, team_code: str) -> float:
    team = match.team_a if team_code == 'a' else match.team_b
    return float(team.tactics.get("attack_dir", +1.0))

def _is_backward_pass(pass_dir: float, dx: float) -> bool:
    """
    Rugby union: pass must be lateral or backwards relative to the passer's team attack direction.
    Here we approximate: along X only vs team attack_dir.
    pass_dir = +1.0 if team attacks to x+, -1.0 if to x-.
    dx = recipient_x - passer_x.
    """
    if pass_dir > 0:
        return dx <= EPS
    else:
        return dx >= -EPS

def perform(player, match):
    """
    Choose a recipient on same team; ensure pass is not forward relative to team attack direction.
    Deterministic outcome via match.rng. On errors, start advantage to opposition and log the law.
    """
    # Only the holder can pass
    holder_code = f"{player.sn}{player.team_code}"
    if match.ball.holder != holder_code:
        return

    team = match.team_a if player.team_code == 'a' else match.team_b
    mates = [p for p in match.players if p.team_code == player.team_code and p is not player]

    px, py, _ = player.location
    attack_dir = _team_attack_dir(match, player.team_code)

    # pick nearest *eligible* recipient (lateral/back only), within 12m
    best = None
    best_d2 = None
    for m in mates:
        mx, my, _ = m.location
        dx = mx - px
        if not _is_backward_pass(attack_dir, dx):
            continue  # forward: illegal
        d2 = (mx - px) ** 2 + (my - py) ** 2
        if d2 <= (12.0 ** 2):
            if best is None or d2 < best_d2:
                best, best_d2 = m, d2

    if not best:
        # No legal target: treat as handling error; release slightly behind and start advantage to opposition
        behind = -0.5 if attack_dir > 0 else +0.5
        match.ball.release()
        match.ball.location = (px + behind, py, 0.0)
        match.last_touch_team = player.team_code
        to = 'b' if player.team_code == 'a' else 'a'
        match.start_advantage("knock_on", to=to, start_x=px, start_y=py)
        log_law(match.tick_count, "handling_error", {"passer": holder_code, "mark": [px, py]}, match=match)
        return

    # Pass success probability from attributes (deterministic roll via match.rng)
    passer_skill = player.attributes.get('technical', {}).get('passing', 60)
    catcher_skill = best.attributes.get('technical', {}).get('catching', 60)
    pressure = 0  # hook up later from nearby defenders
    base_success = 0.85 + (0.001 * (passer_skill + catcher_skill)) - (0.02 * pressure)
    # clamp to [0.1, 0.98] so it’s never impossible/always certain
    base_success = max(0.1, min(0.98, base_success))

    # deterministic RNG key (stable across call order)
    pkey = player.sn * 100 + best.sn
    prob = match.rng.randf("pass_success", match.tick_count, key=pkey)

    if prob < base_success:
        match.ball.holder = f"{best.sn}{best.team_code}"
        match.ball.location = best.location
        match.last_touch_team = player.team_code
        return

    # Drop / knock-on path
    mx, my, _ = best.location
    dx = mx - px
    forward = not _is_backward_pass(attack_dir, dx)  # intended forward = forward-pass offence

    match.ball.release()
    # simulate slight bobble forward if forward, otherwise behind
    bobble = (+0.5 if attack_dir > 0 else -0.5) if forward else (-0.5 if attack_dir > 0 else +0.5)
    match.ball.location = (px + bobble, py, 0.0)
    match.last_touch_team = player.team_code

    to = 'b' if player.team_code == 'a' else 'a'
    match.start_advantage("knock_on", to=to, start_x=px, start_y=py)

    if forward:
        log_law(
            match.tick_count,
            "forward_pass",
            {"passer": holder_code, "receiver": f"{best.sn}{best.team_code}", "mark": [px, py]},
            match=match
        )
    else:
        log_law(
            match.tick_count,
            "knock_on",
            {"passer": holder_code, "receiver": f"{best.sn}{best.team_code}", "mark": [px, py]},
            match=match
        )
