# engine/matchEngine/choice/scrum/common.py
from typing import List, Tuple, Dict, Optional
import random
from team.team_controller import team_by_code
DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

# -----------------------------
# Team & formation helpers
# -----------------------------

def _xyz(p):
    return tuple(p) if isinstance(p, (list,tuple)) and len(p) == 3 else (0.0,0.0,0.0)

def team_possession(match) -> str:
    if getattr(match, "possession", None) in ("a","b"):
        return match.possession
    hid = getattr(match.ball, "holder", None)
    code = hid[-1] if isinstance(hid, str) and hid else "a"
    match.possession = code
    return code

def other(code: str) -> str:
    return "b" if code == "a" else "a"

def dir_sign_for_team(code: str) -> float:
    """
    Attack direction: assume team 'a' attacks +x, 'b' attacks -x (override if you track halves).
    """
    return 1.0 if code == "a" else -1.0

def near_far_touchline_sign(by: float, pitch_half_width: float = 35.0) -> int:
    """
    Choose which side is farther from a touchline (so 7 goes to the far side).
    If by >= 0, far side is negative-y (toward -pitch_half_width); else positive.
    """
    return -1 if by >= 0 else 1

def left_of_attack_vector(ax: float, ay: float) -> Tuple[float, float]:
    """
    Return a unit-ish vector pointing to 'left' of the attack vector.
    If attacking along +x, left is +y; if -x, left is -y.
    """
    # attack vector (ax,0); its left normal is (0, +1) for +x, (0, -1) for -x
    return (0.0, 1.0 if ax >= 0 else -1.0)

def pid_by_jersey(match, team_code: str, jersey: int) -> Optional[str]:
    team = team_by_code(match, team_code)
    if not team:
        return None
    player = team.get_player_by_rn(jersey)
    if not player:
        return None
    return getattr(player, "pid", None) 

def pids_pack(match, team_code: str) -> Dict[int, Optional[str]]:
    """
    Map jersey (1..8 + 9) -> pid; 9 is SH.
    """

    team = team_by_code(match, team_code)
    out: Dict[int, Optional[str]] = {}
    if not team:
        return out
    for j in range(1, 16):
        
        player = team.get_player_by_rn(j)
        pid = getattr(player, "pid", None) or getattr(player, "id", None) if player else None
        out[j] = pid
    return out

def formation_scrum_positions(center: Tuple[float,float,float], attack_sign: float, far_side_sign: int) -> Dict[int, Tuple[float,float,float]]:
    """
    Build canonical scrum offsets around center (bx,by).
    Pack shape:
        1,2,3
         4,5
        6,8,7   (7 on side farthest from touchline)
    9 stands on ATTACKING LEFT of the scrum (tunnel side).
    Distances are small, normalized units; scale to your world later if needed.
    """
    bx, by, _ = center
    # basic spacing
    row_dx = 0.6   * -attack_sign   # front row slightly toward defending side pre-engage
    gap    = 0.5
    depth  = 0.6

    # y offsets: we put 7 on far side; 6 near side
    near = -far_side_sign
    far  = far_side_sign

    pos = {
        2: (bx + row_dx,            by,              0.0),           # hooker
        1: (bx + row_dx,            by + gap,        0.0),
        3: (bx + row_dx,            by - gap,        0.0),

        4: (bx + row_dx - depth,    by + gap/2.0,    0.0),
        5: (bx + row_dx - depth,    by - gap/2.0,    0.0),

        6: (bx + row_dx - 2*depth,  by + 0.9*near,   0.0),
        8: (bx + row_dx - 2*depth,  by,              0.0),
        7: (bx + row_dx - 2*depth,  by + 0.9*far,    0.0),
    }

    # 9 on attacking-left side of the tunnel
    leftx, lefty = left_of_attack_vector(attack_sign, 0.0)
    pos[9] = (bx + 0.2*leftx, by + 0.9*lefty, 0.0)
    return pos

def backs_line_positions(center: Tuple[float,float,float], attack_sign: float) -> List[Tuple[int, Tuple[float,float,float]]]:
    """
    Very light shell: backs (10-15) on a flat line ~5 units back from the ball along -attack dir.
    """
    bx, by, _ = center
    back_dist = 5.0
    base_x = bx - attack_sign * back_dist
    # simple stagger across y
    ys = [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0]  # 10..15
    return [(10+i, (base_x, by + ys[i], 0.0)) for i in range(6)]

def move_pack_and_9_calls(match, team_code: str) -> List[DoCall]:
    """
    Emit DoCalls to position the eight + 9 for team_code. Also place the other pack mirrored around center.
    """
    bx, by, bz = _xyz(getattr(match.ball, "location", None))
    center = (bx, by, 0.0)
    atk = team_code
    defn = other(atk)
    sgn = dir_sign_for_team(atk)
    far_sign = near_far_touchline_sign(by)

    pos_atk = formation_scrum_positions(center, sgn, far_sign)
    pos_def = formation_scrum_positions(center, -sgn, far_sign)  # mirror on engage vector

    def calls_for(team, pos_map: Dict[int, Tuple[float,float,float]]) -> List[DoCall]:
        ids = pids_pack(match, team)
        out: List[DoCall] = []
        for j in (1,2,3,4,5,6,7,8,9):
            pid = ids.get(j)
            if not pid: continue
            tgt = pos_map.get(j)
            if not tgt: continue
            out.append((pid, ("move", None), tgt, tgt))
        # backs line (10..15)
        for j, tgt in backs_line_positions(center, dir_sign_for_team(team)):
            pid = ids.get(j)
            if pid:
                out.append((pid, ("move", None), tgt, tgt))
        return out

    calls: List[DoCall] = []
    calls += calls_for(atk, pos_atk)
    calls += calls_for(defn, pos_def)
    return calls

# -----------------------------
# Scoring / gates (stubs)
# -----------------------------

class ScrumScore:
    """
    Container to accumulate the stage score. You can swap compute hooks later.
    """
    def __init__(self):
        self.value = 0.5
        self.lock_out = False

def compute_stage_1(match, atk_code: str, s: ScrumScore) -> None:
    # 1. score = (rn-2(leadership)**2) * (rn-1(scrum) + rn-3(scrum)) / 3
    # Placeholder: attach real computations later
    s.value += 0.0

def compute_stage_2(match, atk_code: str, s: ScrumScore) -> None:
    # 2. += rn-1(scrum*strength) * rn-3(scrum*strength)
    s.value += 0.0

def compute_stage_3(match, atk_code: str, s: ScrumScore) -> None:
    # 3. += (pack_weight/1000) * (rn-1(scrum)+rn-3(scrum)) * random()
    s.value += 0.0
    # lock_out chance
    """"
    if random.random() > 0.5:
        s.lock_out = True
    """
    return None

def tactic_decision(match, atk_code: str, s: ScrumScore, tactic: str) -> str:
    """
    Return 'take_out' or 'scrum_on' per your thresholds:
      - channel1: take out if score > -0.75; else scrum_on
      - mixed:    scrum_on if score > 0.5 or score < -0.75; else take_out
      - leave_in: take out only if -0.75 < score < -0.25; else scrum_on
    """
    return "take_out"
    

def compute_drive_increment(match, atk_code: str) -> float:
    # 5. += ((rn-3(s*s*a)+rn-1(s*s*a)+rn-2(s*s*a)/2 + rn-4(d*s) + rn-5(d*s)*1.5)/5)
    return 0.0

def counter_shove_check(match, atk_code: str) -> Tuple[float,float]:
    """
    feeding_scrum  = rn-1(strength*weight/150) * rn-3(strength*weight/150)
    opposing_scrum = rn-3(aggression*scrum/150) * rn-3(aggression*scrum/150)
    Return tuple (feeding_val, opposing_val). Stubbed to zeros.
    """
    return (0.0, 0.0)

def outcome_from_score(val: float) -> Optional[str]:
    """
    Return 'pen_feed', 'pen_def', or None.
    + feed team are '+', opp are '-':
      if score > +1   -> penalty to feeding team
      if score < -1   -> penalty to opposition
    """
    if val > 1.0:  return "pen_feed"
    if val < -1.0: return "pen_def"
    return None
