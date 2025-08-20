# utils/player/dh_assign.py
def assign_dummy_half(match, side: str, near_xy=None, prefer_rn9=True, max_dist=10.0):
    cx, cy = (near_xy if near_xy else match.ball.location[:2])
    # prefer 9 if not in ruck and close
    if prefer_rn9:
        nine = next((p for p in match.players if p.team_code==side and p.rn==9), None)
        if nine and not nine.state_flags.get("in_ruck", False):
            dx, dy = nine.location[0]-cx, nine.location[1]-cy
            if dx*dx + dy*dy <= max_dist*max_dist:
                nine.state_flags["dummy_half"] = True
                return f"{nine.sn}{nine.team_code}"
    # fallback: nearest same-side not-in-ruck
    cand = [p for p in match.players if p.team_code==side and not p.state_flags.get("in_ruck", False)]
    if not cand: return None
    cand.sort(key=lambda p:(p.location[0]-cx)**2 + (p.location[1]-cy)**2)
    cand[0].state_flags["dummy_half"] = True
    return f"{cand[0].sn}{cand[0].team_code}"
