# utils/core/logger.py
import json

def _pcode(player) -> str:
    return f"{player.sn}{player.team_code}"
# utils/core/logger.py
import json, sys

def log_tick(tick_count, match):
    # everything to STDERR so it won't pollute the IPC stream
    print(f"[TICK {tick_count}] Ball: {match.ball.location} held by {match.ball.holder or 'None'}",
          file=sys.stderr, flush=True)

    holder_code = match.ball.holder
    if holder_code and hasattr(match, "get_player_by_code"):
        holder = match.get_player_by_code(holder_code)
        if holder:
            dir_a = getattr(getattr(match, "team_a", None), "tactics", {}).get("attack_dir")
            dir_b = getattr(getattr(match, "team_b", None), "tactics", {}).get("attack_dir")
            print(f"   dirs A/B: {dir_a}/{dir_b} | holder {holder.sn}{holder.team_code} at {holder.location}",
                  file=sys.stderr, flush=True)

    for p in getattr(match, "players", []):
        act = getattr(p, "current_action", None) or getattr(p, "action", None) or "idle"
        print(f"  - {p.sn}{p.team_code} ({p.name}): {act} at {p.location},",
              file=sys.stderr, flush=True)


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
# utils/core/logger.py

LEGACY_PREFIX = "__IPC__::match-tick::"

def serialize_tick(match):
    # mirror the original shape as closely as possible
    return {
        "tick": match.tick_count,
        "time": match.match_time,
        "score": match.scoreboard,
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
                "action": p.action,
                "location": p.location,
               "orientation": p.orientation_deg,
            }
            for p in match.players
        ],
        "state": _state_tag(match),  # falls back to current_state.name like before
    }


def dump_tick_json(match, *, flush=True):
    blob = serialize_tick(match)  # or serialize_tick_legacy(...) if you prefer that shape
    print(json.dumps(blob, separators=(",", ":"), ensure_ascii=False), flush=flush)
    return blob


def analyse_ticks(ticks: list[dict]) -> list[tuple[str, float, float]]:
    """Summarise state durations from a sequence of tick snapshots.

    Args:
        ticks: Iterable of tick dictionaries as emitted by ``serialize_tick``.

    Returns:
        A list of ``(state, start_time, duration)`` tuples ordered chronologically.
    """

    timeline: list[tuple[str, float, float]] = []
    if not ticks:
        print(f"{'State':<30} {'Start (s)':>10} {'Duration (s)':>12}")
        return timeline

    last_state: str | None = None
    state_start_time: float | None = None
    final_match_time = 0.0

    for tick in ticks:
        state = tick.get("state")
        state_label = "<unknown>" if state is None else str(state)
        raw_time = tick.get("time")
        current_time = float(raw_time) if raw_time is not None else final_match_time
        final_match_time = current_time

        if last_state is None:
            last_state = state_label
            state_start_time = current_time
            continue

        if state_label != last_state:
            # Close out the previous state using the start time of the new state
            duration = max(0.0, current_time - (state_start_time or 0.0))
            timeline.append((last_state, state_start_time or 0.0, duration))
            last_state = state_label
            state_start_time = current_time

    if last_state is not None:
        duration = max(0.0, final_match_time - (state_start_time or 0.0))
        timeline.append((last_state, state_start_time or 0.0, duration))

    # Print a simple table view for debugging/CLI usage
    header = f"{'State':<30} {'Start (s)':>10} {'Duration (s)':>12}"
    print(header)
    for state, start, duration in timeline:
        print(f"{state:<30} {start:>10.2f} {duration:>12.2f}")

    return timeline
