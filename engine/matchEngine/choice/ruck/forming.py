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

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

R_ENTER = 1.0     # within 1m => enter ruck (attack side non-DH)
R_PULL = 10.0     # defenders may join if score <= 0 inside 10m
R2 = R_ENTER * R_ENTER
R10_2 = R_PULL * R_PULL

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
    if score <= 0.0:
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

    return calls


