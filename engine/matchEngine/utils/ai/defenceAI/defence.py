# utils/defenceAI/defense.py
from typing import Dict, List, Optional, Tuple
from constants import LINE_DEPTH, DEF_MIN_LAT_GAP, TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y

def assign_primary_tackler(ball_xy: Tuple[float,float], defenders: List[object], ctx) -> Optional[int]:
    """
    Prefer nearest defender within 25m and not >10m ahead of ball from ATTACK POV.
    """
    bx, by = ball_xy
    att_dir = ctx["teams"][ctx["ball"]["holder_code"][-1]]["dir"] if ctx["ball"]["holder_code"] else +1.0
    cands = []
    for d in defenders:
        x, y, _ = d.location
        dx, dy = x - bx, y - by
        d2 = dx*dx + dy*dy
        cands.append((d, d2, dx, dy))
    cands.sort(key=lambda t: (t[1], t[0].rn, t[0].sn))
    cands = cands[:ctx["caps"]["MAX_DEF_CONSIDERED"]]
    for d, d2, dx, _ in cands:
        if d2 <= 25*25 and 0.0 <= (dx * att_dir) <= 10.0:
            return d.sn
    return cands[0][0].sn if cands else None

def shape_defensive_line(ball_xy, defenders, ctx, style="drift"):
    bx, by = ball_xy
    # Use ATTACKERS' direction; place line in front of the ball toward them
    holder_code = ctx["ball"]["holder_code"]
    att_dir = ctx["teams"][holder_code[-1]]["dir"] if holder_code else +1.0
    line_x = bx + att_dir * LINE_DEPTH  # ← plus, not minus

    defs = sorted(defenders, key=lambda p: (p.location[1], p.rn, p.sn))
    out, last_y = {}, None
    for d in defs:
        _, y, _ = d.location
        ty = y

        # Overlap prevention first
        if last_y is not None and abs(ty - last_y) < DEF_MIN_LAT_GAP:
            ty = last_y + (DEF_MIN_LAT_GAP if ty >= last_y else -DEF_MIN_LAT_GAP)

        # Light drift relative to ball Y
        if style == "drift":
            if ty > by:  ty += 0.5
            if ty < by:  ty -= 0.5

        ty = max(TOUCHLINE_BOTTOM_Y, min(TOUCHLINE_TOP_Y, ty))
        out[d.sn] = (line_x, ty, 0.0)
        last_y = ty
    return out



def place_backfield_cover(defenders: List[object], ctx) -> List[int]:
    """
    Nominate 15 plus far-side wing relative to ball Y.
    """
    by = ctx["ball"]["y"]
    fullback = next((p for p in defenders if p.rn == 15), None)
    wing_low = next((p for p in defenders if p.rn == 11), None)
    wing_high = next((p for p in defenders if p.rn == 14), None)
    sns = []
    if fullback:
        sns.append(fullback.sn)
    if by < ( (TOUCHLINE_BOTTOM_Y + TOUCHLINE_TOP_Y) / 2.0 ) and wing_high:
        sns.append(wing_high.sn)
    elif wing_low:
        sns.append(wing_low.sn)
    return sns
