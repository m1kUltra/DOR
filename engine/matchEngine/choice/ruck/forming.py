"""forming is where the ruck logic takes place.
decides whether a player enters a ruck or gets inot position
if attacking and no one is there in your team move to ruck
if 1 and score is less than 0.5 nearest person move to ruck (if not sn.9)
if score less than 0 and within 10m move to ruck even if sn.9

players within 1m that are not the dh will enter the ruck for the attack but players will 
only enter the ruck for that defending side if score is =<0

if the player is the first player in and a defender the ruck they will jackal else everyone else just does action clearout for now



 """
# engine/matchEngine/choice/ruck/forming.py
from typing import List, Tuple, Optional
import random
DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

R_ENTER = 1.0     # within 1m => enter ruck (attack side non-DH)
R_PULL = 10.0     # defenders may join if score <= 0 inside 10m
R2 = R_ENTER * R_ENTER
R10_2 = R_PULL * R_PULL
JACKAL_TIME_SCALE = 4.0
def _xyz(p): 
    return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def _d2(ax, ay, bx, by): 
    dx, dy = ax-bx, ay-by
    return dx*dx + dy*dy

def _engagement_score(match, atk: str, bx: float, by: float) -> float:
    """Very simple heuristic you can swap later."""
    # attackers near base – defenders near base
    a = d = 0
    for p in match.players:
        d2 = _d2(p.location[0], p.location[1], bx, by)
        if d2 <= (2.5*2.5):
            if p.team_code == atk: a += 1
            else: d += 1
    return (a - d) * 0.6  # tunable scaling

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = getattr(match, "possession", "a")
    # per‑tick upkeep for ruck timers / cooldowns
    tps = getattr(match, "ticks_per_second", 20)
    dt = 1.0 / max(1, tps)
    for p in match.players:
        if p.state_flags.get("in_ruck") and not p.state_flags.get("off_feet"):
            p.state_flags["time_in_ruck"] = p.state_flags.get("time_in_ruck", 0.0) + dt
        else:
            p.state_flags["time_in_ruck"] = 0.0
        if p.state_flags.get("counter_cooldown", 0) > 0:
            p.state_flags["counter_cooldown"] = p.state_flags.get("counter_cooldown", 0) - 1

    # compute score
    score = _engagement_score(match, atk, bx, by)

    # find DH (don’t enter ruck)
    dh_id = None
    for p in match.players:
        if p.state_flags.get("dummy_half"):
            dh_id = f"{p.sn}{p.team_code}"
            break

    calls: List[DoCall] = []

    # mark clears; we’ll set in_ruck per rules below
    

    # attacker side logic
    attackers = [p for p in match.players if p.team_code == atk]
    defenders = [p for p in match.players if p.team_code != atk]

    # if no attacker near base, nearest attacker moves to base
    if not any(_d2(p.location[0], p.location[1], bx, by) <= R2 for p in attackers):
        # nearest attacker (not DH) heads to ruck
        att_sorted = sorted(attackers, key=lambda p: _d2(p.location[0], p.location[1], bx, by))
        for p in att_sorted:
            pid = f"{p.sn}{p.team_code}"
            if pid == dh_id: 
                continue
            calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))
            break

    # if exactly 1 attacker at base and score < 0.5, nearest extra (not 9) joins
    a_at_base = [p for p in attackers if _d2(p.location[0], p.location[1], bx, by) <= R2]
    if len(a_at_base) == 1 and score < 0.5:
        extra = sorted([p for p in attackers if f"{p.sn}{p.team_code}" != dh_id],
                       key=lambda p: _d2(p.location[0], p.location[1], bx, by))
        if extra:
            pid = f"{extra[0].sn}{extra[0].team_code}"
            calls.append((pid, ("move", None), _xyz(extra[0].location), match.pitch.clamp_position((bx, by, 0.0))))

    # if score < 0 and within 10m, attackers (even 9) may join
    if score < 0.0:
        pack = sorted(attackers, key=lambda p: _d2(p.location[0], p.location[1], bx, by))
        for p in pack:
            if _d2(p.location[0], p.location[1], bx, by) <= R10_2:
                pid = f"{p.sn}{p.team_code}"
                calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))
                # don’t over-fill; next ticks will re-evaluate

    # auto-bind attackers at ≤1m except DH
    for p in attackers:
        if _d2(p.location[0], p.location[1], bx, by) <= R2:
            if f"{p.sn}{p.team_code}" != dh_id:
                p.state_flags["in_ruck"] = True

    # defenders: only enter if score <= 0
    rstate = getattr(match, "ruck_state", {})
    if score <= 0.0 and not rstate.get("won"):
        ds = sorted(defenders, key=lambda p: _d2(p.location[0], p.location[1], bx, by))
        for i, p in enumerate(ds):
            d2 = _d2(p.location[0], p.location[1], bx, by)
            if d2 <= R10_2:
                pid = f"{p.sn}{p.team_code}"
                calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))
                # first defender in ⇒ jackal, others clearout (flag only for now)
                if d2 <= R2:
                    p.state_flags["in_ruck"] = True
                    if not any(q.state_flags.get("jackal") for q in defenders):
                        p.state_flags["jackal"] = True
    # --- Jackal scoring & penalty check ---
    for p in defenders:
        if not p.state_flags.get("jackal"):
            continue
        if p.state_flags.get("counter_cooldown", 0) > 0:
            continue
        rucking = p.norm_attributes.get("rucking", 0.0)
        balance = p.norm_attributes.get("balance", 0.0)
        t = p.state_flags.get("time_in_ruck", 0.0)
        jackal_success = (rucking ** 2 * balance) * (t / JACKAL_TIME_SCALE)
        p.state_flags["jackal_success"] = jackal_success
        if jackal_success >= 1.0:
            match.pending_penalty = {"mark": (bx, by), "to": p.team_code, "reason": "jackal"}
            match.ball.set_action("penalty")
            p.state_flags["counter_cooldown"] = int(2 * tps)

    # --- Barge counter logic ---
    barge_ds = [p for p in defenders
                if p.state_flags.get("in_ruck") and not p.state_flags.get("jackal")
                and not p.state_flags.get("off_feet")
                and p.state_flags.get("counter_cooldown", 0) <= 0]

    if len(barge_ds) >= 2:
        atk_rs = [p for p in attackers if p.state_flags.get("in_ruck") and not p.state_flags.get("off_feet")]
        def _val(player):
            na = player.norm_attributes
            return (
                na.get("aggression", 0.0)
                * na.get("rucking", 0.0)
                * na.get("determination", 0.0)
                * na.get("strength", 0.0)
            )
        att_val = sum(_val(p) for p in atk_rs[: len(barge_ds) + 1])
        def_val = sum(_val(p) for p in barge_ds)
        round_score = att_val * (random.random() ** (1 / 3)) - def_val * (random.random() ** (1 / 3))
        match._barge_score = getattr(match, "_barge_score", 0.0) + round_score
        match._barge_round = getattr(match, "_barge_round", 0) + 1
        for p in barge_ds:
            p.state_flags["counter_cooldown"] = int(2 * tps)
        if match._barge_round >= 3:
            if match._barge_score < -0.5:
                # defenders drive over ball
                match.possession = "b" if atk == "a" else "a"
                match.ball.set_action("turnover")
            match._barge_round = 0
            match._barge_score = 0.0
    else:
        match._barge_round = 0
        match._barge_score = 0.0

    return calls


