# matchEngine/choice/team/attack_choices.py
from typing import List, Tuple, Optional
from constants import FORWARDS, BACKS
from states.open_play import OPEN_PLAY_TAGS

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]
DoCall = Tuple[str, Action, XYZ, XYZ]   # (player_id, action, location, target)

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def plan(match, state_tuple) -> List[DoCall]:
    """
    Very light attacking shape:
      - choose team in possession
      - exclude ball holder + locked defender + anyone in a tackle
      - backs: line behind ball with lateral gaps
      - forwards: two pods near ball, left/right
    """
    tag, _loc, _ctx = state_tuple
    if not (isinstance(tag, str) and tag in OPEN_PLAY_TAGS):
        return []

    # who’s attacking?
    team = match.team_a if match.team_a.in_possession else (match.team_b if match.team_b.in_possession else None)
    if team is None:
        return []

    team_code = "a" if team is match.team_a else "b"
    holder_id = getattr(match.ball, "holder", None)
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    # tactics (already set in setup.py)
    t = team.tactics
    t = (getattr(team, "tactics", None) or {})
    attack_dir   = float(t.get("attack_dir", +1.0))
    depth10      = float(t.get("attack_depth_10", 7.0))            # deeper pivot
    min_behind   = float(t.get("backline_min_behind", 3.0))        # others behind ball
    gap          = float(t.get("backline_lateral_gap", 7.0))       # lateral spacing
    pod_gap      = float(t.get("pod_gap", 6.0))                    # pods left/right
    pod_depth    = float(t.get("pod_depth", 2.0))                  # pods just behind ball
    def _eligible(p) -> bool:
        if p.team_code != team_code: return False
        if holder_id and f"{p.sn}{p.team_code}" == holder_id: return False
        sf = p.state_flags
        if sf.get("locked_defender", False): return False
        if sf.get("tackling", False) or sf.get("being_tackled", False): return False
        return True

    elig = [p for p in match.players if _eligible(p)]
    if not elig:
        return []

    # split backs/forwards
    backs    = [p for p in elig if p.rn in BACKS]
    forwards = [p for p in elig if p.rn in FORWARDS]

    calls: List[DoCall] = []

    # ---- BACKS: shallow line behind the ball ----
    # center around ball.y, with 10 deeper
    pivot = next((p for p in backs if p.rn == 10), None)
    if pivot:
        tx = bx - attack_dir * depth10
        ty = by
        target = match.pitch.clamp_position((tx, ty, 0.0))
        calls.append((f"{pivot.sn}{pivot.team_code}", ("move", None), _xyz(pivot.location), _xyz(target)))
        backs = [p for p in backs if p is not pivot]

    # remaining backs → slots around ball.y: ..., -2*gap, -gap, +gap, +2*gap ...
    backs_sorted = sorted(backs, key=lambda p: p.rn)  # stable-ish
    offsets = []
    for i in range(len(backs_sorted)):
        k = (i // 2) + 1
        offsets.append(-k * gap if i % 2 == 0 else +k * gap)

    for p, off in zip(backs_sorted, offsets):
        tx = bx - attack_dir * min_behind
        ty = by + off
        target = match.pitch.clamp_position((tx, ty, 0.0))
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), _xyz(target)))

    # ---- FORWARDS: two pods near the ball ----
    # alternate left/right of ball.y at pod_gap, shallow depth
    pods = [by - pod_gap, by + pod_gap]
    xf   = bx - attack_dir * pod_depth
    for i, p in enumerate(sorted(forwards, key=lambda p: p.rn)):
        ty = pods[i % 2]
        target = match.pitch.clamp_position((xf, ty, 0.0))
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), _xyz(target)))

    return calls
