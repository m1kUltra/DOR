# utils/core/logger.py
import json

def _pcode(player) -> str:
    return f"{player.sn}{player.team_code}"

def log_tick(tick_count, match):
    print(f"[TICK {tick_count}] Ball: {match.ball.location} held by {match.ball.holder or 'None'}")
    if match.ball.holder:
        holder = match.get_player_by_code(match.ball.holder)
        dir_a = match.team_a.tactics.get("attack_dir")
        dir_b = match.team_b.tactics.get("attack_dir")
        print(f"   dirs A/B: {dir_a}/{dir_b} | holder {holder.sn}{holder.team_code} at {holder.location}")
    for player in match.players:
        print(f"  - {player.sn}{player.team_code} ({player.name}): {player.current_action or 'idle'} at {player.location},")

def log_routing(tick, match, consumed_flag: str, meta: dict):
    dbg = getattr(match, "debug", {})
    if not dbg.get("routing", False):
        return
    print(json.dumps({"routing": {"t": tick, "flag": consumed_flag, "meta": meta or {}}}))

# ---- NEW: state tag resolver that works with BaseState(controller) or legacy ----
def _state_tag(match):
    # Prefer BaseState-style engines: match.engine or match.state with .controller.status
    try:
        eng = getattr(match, "engine", None) or getattr(match, "state", None)
        ctrl = getattr(eng, "controller", None)
        status = getattr(ctrl, "status", None)
        if isinstance(status, (list, tuple)) and len(status) >= 1:
            return status[0]
    except Exception:
        pass
    # Fallback to legacy current_state.name if present
    cs = getattr(match, "current_state", None)
    if cs is not None and hasattr(cs, "name"):
        return cs.name
    return None

def serialize_tick(match):
    return {
        "tick": match.tick_count,
        "time": match.match_time,
        "scoreboard": match.scoreboard,
        "ball": {
            "location": match.ball.location,
            "holder": match.ball.holder,
        },
        "players": [
            {
                "name": p.name,
                "sn": p.sn,
                "rn": p.rn,
                "team_code": p.team_code,
                "action": p.current_action,
                "location": p.location,
                "orientation": p.orientation_deg,
            }
            for p in match.players
        ],
        "state": _state_tag(match),
        "period": match.period,
        # keep if you still populate it elsewhere; harmless if None
        "advantage": getattr(match, "advantage", None),
    }

# ---- NEW: one-liner to print JSON without duplicating logic in Match ----
def dump_tick_json(match, *, flush: bool = True):
    blob = serialize_tick(match)
    print(json.dumps(blob), flush=flush)
    return blob
