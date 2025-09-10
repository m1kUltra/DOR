# engine/matchEngine/choice/scrum/common.py
from typing import List, Tuple, Dict, Optional
import random
from team.team_controller import team_by_code
from utils.probs.scale import scale_factor_lookup

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]

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

def _scale_pow(val: float, exponent: int) -> float:
    """Raise *val* to *exponent* and normalise by the precomputed scale factor."""
    scale = scale_factor_lookup.get(exponent, 1.0)
    try:
        powered = val ** exponent
    except Exception:
        powered = 0.0
    return powered / scale if scale else powered


def compute_stage_1(match, atk_code: str, s: ScrumScore) -> None:
    # 1. score = (rn-2(leadership)**2) * (rn-1(scrum) + rn-3(scrum)) / 3
    # Placeholder: attach real computations later
        def _calc(code: str) -> float:
            team = team_by_code(match, code)
            hook = team.get_player_by_rn(2) if team else None
            prop1 = team.get_player_by_rn(1) if team else None
            prop3 = team.get_player_by_rn(3) if team else None

            leadership = float(getattr(hook, "norm_attributes", {}).get("leadership", 0.0)) if hook else 0.0
            scrum1 = float(getattr(prop1, "norm_attributes", {}).get("scrummaging", 0.0)) if prop1 else 0.0
            scrum3 = float(getattr(prop3, "norm_attributes", {}).get("scrummaging", 0.0)) if prop3 else 0.0

            
            lead_term = _scale_pow(leadership, 2)
            return lead_term * (scrum1 + scrum3) / 3.0

        a = _calc(atk_code)
        b = _calc(other(atk_code))
        scale = max(a, b, 1e-9)
        s.value += (a - b) / scale

def compute_stage_2(match, atk_code: str, s: ScrumScore) -> None:
    # 2. += rn-1(scrum*strength) * rn-3(scrum*strength)
        # 2. += rn-1(scrum*strength) * rn-3(scrum*strength) for both packs
    def prop_product(code: str) -> float:
        team = team_by_code(match, code)
        if not team:
            return 0.0
        p1 = team.get_player_by_rn(1)
        p3 = team.get_player_by_rn(3)

        def norm(player, key: str) -> float:
            return float(getattr(player, "norm_attributes", {}).get(key, 0.0)) if player else 0.0

        p1_scrum = norm(p1, "scrummaging")
        p1_str = norm(p1, "strength")
        p3_scrum = norm(p3, "scrummaging")
        p3_str = norm(p3, "strength")
        return p1_scrum * p1_str * p3_scrum * p3_str

    a = prop_product(atk_code)
    b = prop_product(other(atk_code))
    s.value += a - b

def compute_stage_3(match, atk_code: str, s: ScrumScore) -> None:
    # 3. += (pack_weight/1000) * (rn-1(scrum)+rn-3(scrum)) * random()
    
    def pack_weight(code: str) -> float:
        team = team_by_code(match, code)
        total = 0.0
      
   

        if not team:
        
            return 0.0
     
        for j in range(1, 8):
            p = team.get_player_by_rn(j)
            w = getattr(p, "weight", 0.0) if p else 0.0
            try:
                total += float(w)
            except Exception:
                pass
        
        return total

    def prop_scrum_sum(code: str) -> float:
        team = team_by_code(match, code)
        if not team:
            return 0.0

        def _scrum_norm(p) -> float:
            if not p:
                return 0.0
            attrs = getattr(p, "norm_attributes", {})
            return float(attrs.get("scrummaging") or attrs.get("scrum", 0.0))

        p1 = team.get_player_by_rn(1)
        p3 = team.get_player_by_rn(3)
        return _scrum_norm(p1) + _scrum_norm(p3)

    def_code = other(atk_code)

    atk_term = (pack_weight(atk_code) / 1000.0) * prop_scrum_sum(atk_code) * random.random()
    def_term = (pack_weight(def_code) / 1000.0) * prop_scrum_sum(def_code) * random.random()

    s.value += atk_term - def_term

    if random.random() < 0.5:
        s.lock_out = True

   
  
    return None

def tactic_decision(match, atk_code: str, s: ScrumScore, tactic: str) -> str:
    """
    Return 'take_out' or 'scrum_on' per your thresholds:
      - channel1: take out if score > -0.75; else scrum_on
      - mixed:    scrum_on if score > 0.5 or score < -0.75; else take_out
      - leave_in: take out only if -0.75 < score < -0.25; else scrum_on
    """
    val = s.value
    if tactic == "channel1":
        return "take_out" if val > -0.75 else "scrum_on"
    if tactic == "mixed":
        return "scrum_on" if val > 0.5 or val < -0.75 else "take_out"
    if tactic == "leave_in":
        return "take_out" if -0.75 < val < -0.25 else "scrum_on"
    return "take_out"
    

def compute_drive_increment(match, atk_code: str) -> float:
    # 5. += ((rn-3(s*s*a)+rn-1(s*s*a)+rn-2(s*s*a)/2 + rn-4(d*s) + rn-5(d*s)*1.5)/5)
     
    def team_drive(code: str) -> float:
        team = team_by_code(match, code)
        if not team:
            return 0.0

        def norm_attr(player, key: str) -> float:
            return float(getattr(player, "norm_attributes", {}).get(key, 0.0)) if player else 0.0

        def front_row(player, weight: float = 1.0) -> float:
            if not player:
                return 0.0
            s = norm_attr(player, "scrummaging")
            st = norm_attr(player, "strength")
            a = norm_attr(player, "aggression")
            return weight * s * st * a

        def lock(player, weight: float = 1.0) -> float:
            if not player:
                return 0.0
            d = norm_attr(player, "determination")
            st = norm_attr(player, "strength")
            return weight * d * st

        total = 0.0
        total += front_row(team.get_player_by_rn(3))
        total += front_row(team.get_player_by_rn(1))
        total += front_row(team.get_player_by_rn(2), 0.5)
        total += lock(team.get_player_by_rn(4))
        total += lock(team.get_player_by_rn(5), 1.5)
        return total / 5.0

    atk_val = team_drive(atk_code)
    def_val = team_drive(other(atk_code))
    return atk_val - def_val

def counter_shove_check(match, atk_code: str) -> Tuple[float,float]:
    """
    feeding_scrum  = rn-1(strength*weight/150) * rn-3(strength*weight/150)
    opposing_scrum = rn-3(aggression*scrum/150) * rn-3(aggression*scrum/150)
    Return tuple (feeding_val, opposing_val). Stubbed to zeros.
    """
    
    # Feed side props (1 and 3) combine strength and weight
    feed_vals = []
    for j in (1, 3):
        p = match.get_player_by_code(f"{j}{atk_code}")
        if not p:
            feed_vals.append(0.0)
            continue
        attrs = getattr(p, "norm_attributes", {})
        strength = float(attrs.get("strength", 0.0))
        weight = float(getattr(p, "weight", 0.0) or 0.0) / 150.0
        feed_vals.append(strength * weight)

    feeding_scrum = feed_vals[0] * feed_vals[1] if len(feed_vals) == 2 else 0.0

    # Opposition props rely on aggression and scrum ability
    opp_code = other(atk_code)
    opp_vals = []
    for j in (1, 3):
        p = match.get_player_by_code(f"{j}{opp_code}")
        if not p:
            opp_vals.append(0.0)
            continue
        attrs = getattr(p, "norm_attributes", {})
        aggression = float(attrs.get("aggression", 0.0))
        scrum = float(attrs.get("scrummaging", 0.0) or attrs.get("scrum", 0.0))
        opp_vals.append(aggression * scrum)

    opposing_scrum = opp_vals[0] * opp_vals[1] if len(opp_vals) == 2 else 0.0

    scale = max(feeding_scrum, opposing_scrum, 1e-9)
    return (feeding_scrum / scale, opposing_scrum / scale)


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
