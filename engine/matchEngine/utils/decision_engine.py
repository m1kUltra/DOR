# utils/decision_engine.py
from typing import Dict, Tuple
from utils.context import build_context
from utils.spacing import resolve_team_spacing
from utils.attackAI.offense import choose_offensive_action
from utils.defenceAI.defence import (
    assign_primary_tackler, shape_defensive_line, place_backfield_cover
)
from utils.position_utils import backline_shape_positions, forwards_shape_positions

Action = str
Target = Tuple[float, float, float]

# ---- Rapid fan-out detector (panic spread) ----
BUNCH_RADIUS_M = 5.0
BUNCH_MIN_COUNT = 5

def _needs_rapid_fan(team) -> bool:
    """
    True if any player has >= BUNCH_MIN_COUNT teammates (including self)
    within BUNCH_RADIUS_M (euclidean), i.e., a heavy bunch.
    """
    locs = [(p, p.location) for p in team.squad]
    r2 = BUNCH_RADIUS_M * BUNCH_RADIUS_M
    for _p, (px, py, _pz) in locs:
        close = 0
        for _q, (qx, qy, _qz) in locs:
            dx, dy = (qx - px), (qy - py)
            if dx*dx + dy*dy <= r2:
                close += 1
        if close >= BUNCH_MIN_COUNT:
            return True
    return False


def compute_positions_for_teams(match, game_state) -> Dict[object, Tuple[Action, Target, dict]]:
    ctx = build_context(match)
    holder_code = ctx["ball"]["holder_code"] or ""
    state_name = game_state.name

    # --- ATTACK vs DEFENSE sides ---
    a_is_attack = holder_code.endswith("a")
    b_is_attack = holder_code.endswith("b")

    # --- Build raw proposals (actions + initial targets + meta) ---
    def propose_attack(team):
        out = {}
        bx, by, bz = match.ball.location
        for p in team.squad:
            code = f"{p.sn}{p.team_code}"
            if state_name != "open_play":
                out[p] = (p.current_action or "idle", p.location, {})
                continue
            if code == holder_code:
                out[p] = choose_offensive_action(p, ctx)
                continue

            # propose shape target
            if p.rn in {1,2,3,4,5,6,7,8}:
                f_sorted = sorted([q for q in team.squad if q.rn in {1,2,3,4,5,6,7,8}], key=lambda q:(q.rn,q.sn))
                ordinal = f_sorted.index(p)
                tgt = forwards_shape_positions(team, (bx,by,bz), p.rn, ordinal)
            else:
                b_sorted = sorted([q for q in team.squad if q.rn in {9,10,11,12,13,14,15}], key=lambda q:(q.rn,q.sn))
                ordinal = b_sorted.index(p)
                tgt = backline_shape_positions(team, (bx,by,bz), p.rn, ordinal)

            out[p] = ("shape", tgt, {})
        return out

    def propose_defense(team):
        out = {}
        if state_name != "open_play":
            for p in team.squad:
                out[p] = (p.current_action or "idle", p.location, {})
            return out

        ball_xy = (ctx["ball"]["x"], ctx["ball"]["y"])
        defenders = list(team.squad)

        primary_sn = assign_primary_tackler(ball_xy, defenders, ctx)
        line_targets = shape_defensive_line(ball_xy, defenders, ctx, style="drift")
        cover_sns = set(place_backfield_cover(defenders, ctx))

        for p in team.squad:
            if p.sn == primary_sn:
                out[p] = ("tackle", (ctx["ball"]["x"], ctx["ball"]["y"], 0.0), {})
            elif p.sn in cover_sns:
                tx, ty, _ = line_targets.get(p.sn, (p.location[0], p.location[1], 0.0))
                dir_self = float(team.tactics.get("attack_dir", +1.0))
                tx = tx - 12.0 * dir_self
                out[p] = ("cover", (tx, ty, 0.0), {"lock": True})
            else:
                tgt = line_targets.get(p.sn, p.location)
                out[p] = ("defend", tgt, {})
        return out

    # build proposals
    props_a = propose_attack(match.team_a) if a_is_attack else propose_defense(match.team_a)
    props_b = propose_attack(match.team_b) if b_is_attack else propose_defense(match.team_b)

    # locked roles that spacing must not move
    LOCKED = {"tackle", "cover"}

    def build_exempt(props):
        ex = set()
        for p, (act, _tgt, meta) in props.items():
            code = f"{p.sn}{p.team_code}"
            if code == holder_code or act in LOCKED or (meta and meta.get("lock")):
                ex.add(p)
        return ex

    exempt_a = build_exempt(props_a)
    exempt_b = build_exempt(props_b)

    # --- Rapid fan-out flags (only in open play) ---
    rapid_a = (state_name == "open_play") and _needs_rapid_fan(match.team_a)
    rapid_b = (state_name == "open_play") and _needs_rapid_fan(match.team_b)

    # --- Run spacing with defense/attack mode + panic spread ---
    adj_a = resolve_team_spacing(
        match.team_a,
        {p: tgt for p, (_act, tgt, *_meta) in props_a.items()},
        state_name,
        match.ball.location,
        holder_code,
        exempt=exempt_a,
        mode=("attack" if a_is_attack else "defense"),
        panic_spread=rapid_a,
    )
    adj_b = resolve_team_spacing(
        match.team_b,
        {p: tgt for p, (_act, tgt, *_meta) in props_b.items()},
        state_name,
        match.ball.location,
        holder_code,
        exempt=exempt_b,
        mode=("attack" if b_is_attack else "defense"),
        panic_spread=rapid_b,
    )

    # final map (keep actions/meta, swap in adjusted targets)
    final: Dict[object, Tuple[Action, Target, dict]] = {}

    # guard if spacing unexpectedly returned None
    if adj_a is None:
        adj_a = {p: tgt for p, (_a, tgt, *_m) in props_a.items()}
    if adj_b is None:
        adj_b = {p: tgt for p, (_a, tgt, *_m) in props_b.items()}

    for p, (act, _tgt, meta) in props_a.items():
        final[p] = (act, adj_a.get(p, _tgt), meta or {})
    for p, (act, _tgt, meta) in props_b.items():
        final[p] = (act, adj_b.get(p, _tgt), meta or {})

    return final
