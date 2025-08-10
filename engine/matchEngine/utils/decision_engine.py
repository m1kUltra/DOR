# utils/decision_engine.py
from typing import Dict, Tuple
from utils.context import build_context
from utils.spacing import resolve_team_spacing
from utils.attackAI.offense import choose_offensive_action
from utils.defenceAI.defence import (
    assign_primary_tackler, shape_defensive_line, place_backfield_cover
)

Action = str
Target = Tuple[float, float, float]

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
        for p in team.squad:
            code = f"{p.sn}{p.team_code}"
            if state_name != "open_play":
                out[p] = (p.current_action or "idle", p.location, {})
            elif code == holder_code:
                out[p] = choose_offensive_action(p, ctx)  # may return ("kick", None, {...})
            else:
                # For now, keep attackers’ non‑holders on their proposed shape/spot
                out[p] = ("shape", p.location, {})
        return out

    def propose_defense(team):
        out = {}
        if state_name != "open_play":
            for p in team.squad:
                out[p] = (p.current_action or "idle", p.location, {})
            return out

        ball_xy = (ctx["ball"]["x"], ctx["ball"]["y"])
        defenders = list(team.squad)

        # Compute once per team
        primary_sn = assign_primary_tackler(ball_xy, defenders, ctx)
        line_targets = shape_defensive_line(ball_xy, defenders, ctx, style="drift")
        cover_sns = set(place_backfield_cover(defenders, ctx))

        for p in team.squad:
            if p.sn == primary_sn:
                out[p] = ("tackle", (ctx["ball"]["x"], ctx["ball"]["y"], 0.0), {})
            elif p.sn in cover_sns:
                tx, ty, _ = line_targets.get(p.sn, (p.location[0], p.location[1], 0.0))
                # sit deeper for cover (toward own try line, i.e., opposite attack dir)
                dir_self = float(team.tactics.get("attack_dir", +1.0))
                tx = tx - 12.0 * dir_self
                out[p] = ("cover", (tx, ty, 0.0), {"lock": True})
            else:
                tgt = line_targets.get(p.sn, p.location)
                out[p] = ("defend", tgt, {})
        return out

    props_a = propose_attack(match.team_a) if a_is_attack else propose_defense(match.team_a)
    props_b = propose_attack(match.team_b) if b_is_attack else propose_defense(match.team_b)

    # --- Build exempt sets so spacing skips locked roles & holder ---
    LOCKED = {"tackle", "cover"}  # add more if you introduce fixed-line roles

    def build_exempt(props):
        ex = set()
        for p, (act, _, meta) in props.items():
            code = f"{p.sn}{p.team_code}"
            if code == holder_code or act in LOCKED or (meta and meta.get("lock")):
                ex.add(p)
        return ex

    exempt_a = build_exempt(props_a)
    exempt_b = build_exempt(props_b)

    # --- Run spacing once per team with exemptions applied ---
    adj_a = resolve_team_spacing(
        match.team_a,
        {p: tgt for p, (_, tgt, *_) in props_a.items()},
        state_name,
        match.ball.location,
        holder_code,
        exempt=exempt_a,
    )
    adj_b = resolve_team_spacing(
        match.team_b,
        {p: tgt for p, (_, tgt, *_) in props_b.items()},
        state_name,
        match.ball.location,
        holder_code,
        exempt=exempt_b,
    )

    # --- Build final map using adjusted targets ---
    final: Dict[object, Tuple[Action, Target, dict]] = {}
    for p, (act, _, meta) in props_a.items():
        final[p] = (act, adj_a[p], meta or {})
    for p, (act, _, meta) in props_b.items():
        final[p] = (act, adj_b[p], meta or {})
    return final
