
# set_pieces/scrum.py
# Wireframe scrum handlers that align with states/scrum.py's tags.
# Uses normalized attributes if present; safe defaults otherwise.
from dataclasses import dataclass, field
from typing import Dict, Tuple, Any, Optional
import random

# Optional: your constants; used here only for sign conventions or field layout if needed
# from constants import TOUCHLINE_TOP_Y, TOUCHLINE_BOTTOM_Y

# --- Public API (handlers) ---
def handle_crouch(match, ev): _handler(match, ev, _on_crouch)
def handle_bind(match, ev):   _handler(match, ev, _on_bind)
def handle_set(match, ev):    _handler(match, ev, _on_set)
def handle_feed(match, ev):   _handler(match, ev, _on_feed)
def handle_drive(match, ev):  _handler(match, ev, _on_drive)
def handle_stable(match, ev): _handler(match, ev, _on_stable)
def handle_out(match, ev):    _handler(match, ev, _on_out)

# Stage tags (must match states/scrum.py)
CROUCH = "scrum.crouch"; BIND = "scrum.bind"; SET = "scrum.set"
FEED = "scrum.feed"; DRIVE = "scrum.drive"; STABLE = "scrum.stable"; OUT = "scrum.out"

PEN_FEEDING = "feeding_penalty"
PEN_OPPOSING = "opposing_penalty"

# --- Internal state container ---
@dataclass
class ScrumState:
    score: float = 0.0
    penalty: Optional[str] = None
    lock_out: bool = False
    did_counter: bool = False
    tactic: str = "mixed"    # channel1 | mixed | leave_in
    seed: Optional[int] = None
    rng: Any = field(default_factory=random.Random)
    timeline: list = field(default_factory=list)
    feeding_side: str = "a"  # 'a' or 'b'

# --- Utilities ---
def _get_attrs_from_player(p) -> Dict[str, float]:
    """Pick up attributes from common spots; defaults to 1.0 (weight=110)."""
    def get_from_dict(d, k, default=None):
        if isinstance(d, dict) and k in d: return d[k]
        return default
    def fetch(k, default=1.0):
        for name in ("attributes","ratings","skills","stats"):
            v = get_from_dict(getattr(p, name, None), k, None)
            if v is not None: return float(v)
        if hasattr(p, k): 
            try: return float(getattr(p, k))
            except: return default
        return default
    return {
        "scrum": fetch("scrum", 1.0),
        "strength": fetch("strength", 1.0),
        "aggression": fetch("aggression", 1.0),
        "leadership": fetch("leadership", 1.0),
        "determination": fetch("determination", 1.0),
        "weight": fetch("weight", 110.0),
    }

def _gather_team_attrs(match, side: str) -> Dict[int, Dict[str,float]]:
    team = match.team_a if side == "a" else match.team_b
    attrs: Dict[int, Dict[str,float]] = {}
    for p in getattr(team, "squad", []):
        rn = getattr(p, "rn", None)
        if rn is None: continue
        attrs[int(rn)] = _get_attrs_from_player(p)
    return attrs

def _pack_weight(attrs: Dict[int, Dict[str,float]]) -> float:
    return sum(attrs.get(rn, {}).get("weight", 110.0) for rn in range(1,9))

def _stage_checks(score: float) -> Optional[str]:
    if score > 1.0:  return PEN_FEEDING
    if score < -1.0: return PEN_OPPOSING
    return None

def _tactic_decision(score: float, tactic: str, rng: random.Random, lock_out: bool) -> str:
    if lock_out: return "out_now"
    t = (tactic or "mixed").lower()
    if t == "channel1":
        return "out_now" if score > -0.75 else "scrum_on"
    if t == "mixed":
        if score > 0.5:   return "scrum_on"
        if score < -0.75: return "scrum_on"
        return "out_now"
    if t == "leave_in":
        return "out_now" if (-0.75 < score < -0.25) else "scrum_on"
    return "scrum_on"

# Positioning
def _scrum_positions_attacking(open_side_pos_y=True) -> Dict[int, Tuple[float,float]]:
    dx_front, dx_locks, dx_back = 0.0, -0.8, -1.6
    y_front = [-0.9, 0.0, 0.9]; y_locks = [-0.45, 0.45]; y_back = [0.6, 0.0, 1.0]  # 6,8,7 (+y side)
    if not open_side_pos_y:
        y_front = [-y for y in y_front]; y_locks = [-y for y in y_locks]; y_back = [-y for y in y_back]
    pos = { 1:(dx_front,y_front[0]), 2:(dx_front,y_front[1]), 3:(dx_front,y_front[2]),
            4:(dx_locks,y_locks[0]), 5:(dx_locks,y_locks[1]),
            6:(dx_back,y_back[0]), 8:(dx_back,y_back[1]), 7:(dx_back,y_back[2]),
            9:(-0.4, 1.4 if open_side_pos_y else -1.4) }
    backs_y = [-1.0, -0.66, -0.33, 0.0, 0.33, 0.66]
    for i, rn in enumerate(range(10,16)):
        pos[rn] = (-5.0, backs_y[i]*6.0)  # ~5m back
    return pos
def _mirror_defensive(attack_pos): return {rn:(-x,y) for rn,(x,y) in attack_pos.items()}

# Assign positions in a generic way (non-teleport): store targets on players if available
def _apply_positions(match, feeding_side: str, pos_feed: Dict[int,Tuple[float,float]], pos_opp: Dict[int,Tuple[float,float]]):
    def team_for(side): return match.team_a if side == "a" else match.team_b
    def set_to(team, rn, xy):
        for p in getattr(team, "squad", []):
            if getattr(p, "rn", None) == rn:
                am = getattr(p, "action_meta", None)
                if isinstance(am, dict):
                    am["to"] = (xy[0], xy[1], 0.0)  # TARGET (no teleport)
                else:
                    setattr(p, "action_meta", {"to": (xy[0],xy[1],0.0)})
    atk = team_for(feeding_side)
    dff = team_for("b" if feeding_side == "a" else "a")
    for rn, xy in pos_feed.items(): set_to(atk, rn, xy)
    for rn, xy in pos_opp.items():  set_to(dff, rn, xy)
    # keep a debug copy on match for visualization/tools
    setattr(match, "debug_last_scrum_positions", {"feeding": pos_feed, "opposing": pos_opp})

# Event utility: attempt to push next tag; fall back to storing on match
def _push_next(match, next_tag: str, loc, ctx):
    try:
        import event
        if hasattr(event, "push"): event.push(match, next_tag, loc, ctx)
        elif hasattr(event, "emit"): event.emit(match, next_tag, loc, ctx)
        else: setattr(match, "next_state_tag", (next_tag, loc, ctx))
    except Exception:
        setattr(match, "next_state_tag", (next_tag, loc, ctx))

# Access / init state
def _state(match) -> ScrumState:
    st = getattr(match, "_scrum_state", None)
    if isinstance(st, ScrumState):
        return st
    st = ScrumState()
    st.tactic = getattr(getattr(match, "tactics", None), "scrum_tactic", "mixed") if hasattr(match, "tactics") else "mixed"
    st.seed = getattr(match, "seed", None)
    st.rng = random.Random(st.seed)
    st.feeding_side = getattr(match, "possession", "a")
    setattr(match, "_scrum_state", st)
    # place players initially
    pos_feed = _scrum_positions_attacking(True)
    pos_opp  = _mirror_defensive(pos_feed)
    _apply_positions(match, st.feeding_side, pos_feed, pos_opp)
    return st

# --- Stage handlers ---
def _on_crouch(match, tag, loc, ctx, st: ScrumState):
    feed = _gather_team_attrs(match, st.feeding_side)
    scrum_1 = feed.get(1,{}).get("scrum",1.0); scrum_3 = feed.get(3,{}).get("scrum",1.0)
    lead_2  = feed.get(2,{}).get("leadership",1.0)
    delta = (lead_2**2.0) * ((scrum_1 + scrum_3)/3.0)
    st.score += delta; st.penalty = _stage_checks(st.score)
    st.timeline.append({"stage":"crouch","delta":delta,"score":st.score,"penalty":st.penalty})
    _push_next(match, "scrum.bind" if not st.penalty else "scrum.out", loc, ctx)

def _on_bind(match, tag, loc, ctx, st: ScrumState):
    feed = _gather_team_attrs(match, st.feeding_side)
    s2_l = feed.get(1,{}).get("scrum",1.0)*feed.get(1,{}).get("strength",1.0)
    s2_r = feed.get(3,{}).get("scrum",1.0)*feed.get(3,{}).get("strength",1.0)
    delta = s2_l * s2_r
    st.score += delta; st.penalty = _stage_checks(st.score)
    st.timeline.append({"stage":"bind","delta":delta,"score":st.score,"penalty":st.penalty})
    _push_next(match, "scrum.set" if not st.penalty else "scrum.out", loc, ctx)

def _on_set(match, tag, loc, ctx, st: ScrumState):
    feed = _gather_team_attrs(match, st.feeding_side)
    pack_w = _pack_weight(feed)
    scrum_1 = feed.get(1,{}).get("scrum",1.0); scrum_3 = feed.get(3,{}).get("scrum",1.0)
    delta = (pack_w/1000.0) * (scrum_1 + scrum_3) * st.rng.random()
    st.score += delta
    st.lock_out = (st.rng.random() > 0.5)
    st.timeline.append({"stage":"set","delta":delta,"score":st.score,"lock_out":st.lock_out})
    _push_next(match, "scrum.feed", loc, ctx)

def _on_feed(match, tag, loc, ctx, st: ScrumState):
    decision = _tactic_decision(st.score, st.tactic, st.rng, st.lock_out)
    st.timeline.append({"stage":"feed","decision":decision,"score":st.score})
    if decision == "out_now":
        _push_next(match, "scrum.out", loc, ctx)
    else:
        _push_next(match, "scrum.drive", loc, ctx)

def _on_drive(match, tag, loc, ctx, st: ScrumState):
    feed = _gather_team_attrs(match, st.feeding_side)
    def g(rn,k,default=1.0): return feed.get(rn,{}).get(k,default)
    terms = [
        g(3,"scrum")*g(3,"strength")*g(3,"aggression"),
        g(1,"scrum")*g(1,"strength")*g(1,"aggression"),
        0.5*g(2,"scrum")*g(2,"strength")*g(2,"aggression"),
        g(4,"determination")*g(4,"strength"),
        1.5*g(5,"determination")*g(5,"strength"),
    ]
    delta = sum(terms)/5.0
    st.score += delta; st.penalty = _stage_checks(st.score)
    decision = _tactic_decision(st.score, st.tactic, st.rng, st.lock_out)
    st.timeline.append({"stage":"drive","delta":delta,"decision":decision,"score":st.score,"penalty":st.penalty})
    if st.penalty:
        _push_next(match, "scrum.out", loc, ctx)
    elif decision == "out_now":
        _push_next(match, "scrum.out", loc, ctx)
    else:
        _push_next(match, "scrum.stable", loc, ctx)

def _on_stable(match, tag, loc, ctx, st: ScrumState):
    if not st.did_counter:
        feed = _gather_team_attrs(match, st.feeding_side)
        opp  = _gather_team_attrs(match, "b" if st.feeding_side=="a" else "a")
        str1, w1 = feed.get(1,{}).get("strength",1.0), feed.get(1,{}).get("weight",110.0)
        str3, w3 = feed.get(3,{}).get("strength",1.0), feed.get(3,{}).get("weight",110.0)
        feed_term = (str1*w1/150.0)*(str3*w3/150.0)
        ag3, sc3 = opp.get(3,{}).get("aggression",1.0), opp.get(3,{}).get("scrum",1.0)
        opp_term = (ag3*sc3/150.0)*(ag3*sc3/150.0)
        delta = feed_term*(st.rng.random()**(1/3)) - opp_term*(st.rng.random()**(1/3))
        st.score += delta; st.penalty = _stage_checks(st.score)
        st.timeline.append({"stage":"stable_counter_shuv","delta":delta,"score":st.score,"penalty":st.penalty})
        st.did_counter = True
    _push_next(match, "scrum.out", loc, ctx)

def _on_out(match, tag, loc, ctx, st: ScrumState):
    # Ball is at the back; expose a compact result for downstream handler (9 pass / 8 pick).
    outcome = "won_clean" if st.score >= 0 and not st.penalty else ("reset" if st.penalty else "won_under_pressure")
    result = {
        "timeline": st.timeline,
        "final_score": st.score,
        "penalty": st.penalty,
        "lock_out": st.lock_out,
        "outcome": outcome,
        "possession": "feeding",
    }
    setattr(match, "debug_last_scrum_result", result)
    # No next push here; leave to game FSM (open play, 9 pass, etc.).

# Generic handler wrapper: ensures state, applies positions once, then runs stage fn.
def _handler(match, ev, fn):
    tag, loc, ctx = ev
    st = _state(match)
    # Ensure positions are set at entry (once)
    if not getattr(match, "_scrum_positions_applied", False):
        pos_feed = _scrum_positions_attacking(True)
        pos_opp  = _mirror_defensive(pos_feed)
        _apply_positions(match, st.feeding_side, pos_feed, pos_opp)
        setattr(match, "_scrum_positions_applied", True)
    fn(match, tag, loc, ctx, st)
