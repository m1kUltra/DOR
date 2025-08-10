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
    """
    Thin orchestrator:
      - builds ctx once
      - delegates holder to offense chooser
      - delegates all others to defense shapers
      - runs spacing and returns {player: (action, target, meta)}
    """
    ctx = build_context(match)
    holder_code = ctx["ball"]["holder_code"] or ""

    def propose(team_self, team_opp):
        out = {}
        ball_xy = (ctx["ball"]["x"], ctx["ball"]["y"])
        defenders = list(team_self.squad)  # this side's players (if defending this tick)
        for p in team_self.squad:
            code = f"{p.sn}{p.team_code}"
            if game_state.name != "open_play":
                out[p] = (p.current_action or "idle", p.location, {})
                continue
            if code == holder_code:
                out[p] = choose_offensive_action(p, ctx)
            else:
                primary = assign_primary_tackler(ball_xy, defenders, ctx)
                line_targets = shape_defensive_line(ball_xy, defenders, ctx, style="drift")
                cover_sns = set(place_backfield_cover(defenders, ctx))
                if p.sn == primary:
                    out[p] = ("tackle", (ctx["ball"]["x"], ctx["ball"]["y"], 0.0), {})
                elif p.sn in cover_sns:
                    tx, ty, _ = line_targets.get(p.sn, (p.location[0], p.location[1], 0.0))
                    tx = tx - 12.0 * float(team_self.tactics.get("attack_dir", +1.0))  # sit deeper for cover
                    out[p] = ("cover", (tx, ty, 0.0), {})
                else:
                    tgt = line_targets.get(p.sn, p.location)
                    out[p] = ("defend", tgt, {})
        return out

    props_a = propose(match.team_a, match.team_b)
    props_b = propose(match.team_b, match.team_a)

    adj_a = resolve_team_spacing(
        match.team_a,
        {p: tgt for p, (_, tgt, *_) in props_a.items()},
        game_state.name,
        match.ball.location,
        holder_code,
    )
    adj_b = resolve_team_spacing(
        match.team_b,
        {p: tgt for p, (_, tgt, *_) in props_b.items()},
        game_state.name,
        match.ball.location,
        holder_code,
    )

    final: Dict[object, Tuple[Action, Target, dict]] = {}
    for p, (act, _, meta) in props_a.items():
        final[p] = (act, adj_a[p], meta or {})
    for p, (act, _, meta) in props_b.items():
        final[p] = (act, adj_b[p], meta or {})
    return final
