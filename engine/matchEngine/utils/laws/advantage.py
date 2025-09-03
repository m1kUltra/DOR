# matchEngine/utils/advantage.py

TIME_LIMITS = {
    "knock_on": 5.0,
    "penalty": 8.0,
}

METERS_LIMITS = {
    "knock_on": 10.0,
    "penalty": 20.0,
}

def start(current_adv: dict | None, *, type_: str, to: str, start_x: float, start_y: float, start_t: float, reason: str | None = None) -> dict | None:
    """
    Start an advantage overlay if none is active.
    Returns the new advantage dict (or the existing one if already running).
    """
    if current_adv is not None:
        return current_adv  # Phase 1: do not stack
    return {
        "type": type_,
        "to": to,
        "start_t": float(start_t),
        "start_x": float(start_x),
        "start_y": float(start_y),
        "timer_s": 0.0,
        "meters": 0.0,
        "reason": reason or type_,
    }

def _meters_from(bx: float, start_x: float, attack_dir: float) -> float:
    return max(0.0, (bx - start_x) * float(attack_dir))

def tick(
    adv: dict | None,
    *,
    match_time: float,
    ball_x: float,
    attack_dir: float,
    holder_team: str | None = None
) -> tuple[dict | None, dict | None, str | None]:
    """
    Advance the advantage overlay by time and meters.

    Returns (new_adv, flag_dict, outcome)
      - new_adv: updated advantage or None if ended
      - flag_dict: a pending_* flag to set when calling back (or None)
      - outcome: "realized" | "called_back" | None
    """
    if adv is None:
        return None, None, None

    type_ = adv["type"]
    time_limit = TIME_LIMITS.get(type_, 5.0)
    meters_limit = METERS_LIMITS.get(type_, 10.0)

    # update snapshot
    adv = dict(adv)
    adv["timer_s"] = max(0.0, match_time - adv["start_t"])
    adv["meters"]  = _meters_from(ball_x, adv["start_x"], attack_dir)

    # 1) Realized by meters → end, no flag
    if adv["meters"] >= meters_limit:
        return None, None, "realized"

    # 2) Possession flipped to offending side → call back NOW with flag
    if holder_team and holder_team != adv["to"]:
        if type_ == "knock_on":
            flag = {"pending_scrum": {
                "x": adv["start_x"], "y": adv["start_y"],
                "put_in": adv["to"], "reason": adv.get("reason", "knock_on")
            }}
        elif type_ == "penalty":
            flag = {"pending_penalty": {
                "mark": (adv["start_x"], adv["start_y"]),
                "to": adv["to"], "reason": adv.get("reason", "penalty")
            }}
        else:
            flag = None
        return None, flag, "called_back"

    # 3) Timed out → call back with flag
    if adv["timer_s"] >= time_limit:
        if type_ == "knock_on":
            flag = {"pending_scrum": {
                "x": adv["start_x"], "y": adv["start_y"],
                "put_in": adv["to"], "reason": adv.get("reason", "knock_on")
            }}
            return None, flag, "called_back"
        if type_ == "penalty":
            flag = {"pending_penalty": {
                "mark": (adv["start_x"], adv["start_y"]),
                "to": adv["to"], "reason": adv.get("reason", "penalty")
            }}
            return None, flag, "called_back"

    # 4) Still playing advantage
    return adv, None, None

