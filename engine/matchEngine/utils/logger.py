def log_tick(tick_count, match):
    print(f"[TICK {tick_count}] Ball: {match.ball.location} held by {match.ball.holder or 'None'}")
    if match.ball.holder:
        holder = match.get_player_by_code(match.ball.holder)
        dir_a = match.team_a.tactics.get("attack_dir")
        dir_b = match.team_b.tactics.get("attack_dir")
        print(f"   dirs A/B: {dir_a}/{dir_b} | holder {holder.sn}{holder.team_code} at {holder.location}")
    for player in match.players:
        print(f"  - {player.sn}{player.team_code} ({player.name}): {player.current_action or 'idle'} at {player.location}")


# ---- NEW: focused loggers ----

import json

def _pcode(player) -> str:
    return f"{player.sn}{player.team_code}"

def log_decision(tick, player, choice: str, scores: dict | None = None, state_name: str | None = None):
    """
    Minimal, cheap decision log. Only pass `scores` if the caller’s DEBUG flag says so.
    """
    payload = {
        "t": tick,
        "p": _pcode(player),
        "state": state_name or "",
        "choice": choice,
    }
    if scores is not None:
        payload["scores"] = scores
    print(json.dumps({"decision": payload}))


def log_routing(tick, match, consumed_flag: str, meta: dict):
    """
    E.g., consumed_flag="pending_scrum", meta={"x":..,"y":..,"put_in":"a"}
    """
    # cheap guard
    dbg = getattr(match, "debug", {})
    if not dbg.get("routing", False):
        return
    print(json.dumps({"routing": {
        "t": tick,
        "flag": consumed_flag,
        "meta": meta or {}
    }}))


def log_law(tick, event: str, meta: dict, match=None):
    """
    E.g., event="forward_pass", meta={"passer":"9a","receiver":"12a","mark":[x,y]}
    """
    # cheap guard
    dbg = getattr(match, "debug", {}) if match is not None else {}
    if match is not None and not dbg.get("laws", False):
        return
    print(json.dumps({"law": {
        "t": tick,
        "event": event,
        "meta": meta or {}
    }}))
