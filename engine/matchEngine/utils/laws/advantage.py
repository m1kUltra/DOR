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

def tick(adv: dict | None, *, match_time: float, ball_x: float, attack_dir: float) -> tuple[dict | None, dict | None, str | None]:
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

    adv = dict(adv)  # copy
    adv["timer_s"] = max(0.0, match_time - adv["start_t"])
    adv["meters"] = _meters_from(ball_x, adv["start_x"], attack_dir)

    # Realized by meters
    if adv["meters"] >= meters_limit:
        return None, None, "realized"

    # Called back by time
    if adv["timer_s"] >= time_limit:
        if type_ == "knock_on":
            flag = {"pending_scrum": {"x": adv["start_x"], "y": adv["start_y"], "put_in": adv["to"], "reason": adv.get("reason", "knock_on")}}
        if type_ == "penalty":
            flag = {"pending_penalty": {"mark": (adv["start_x"], adv["start_y"]), "to": adv["to"], "reason": "penalty"}}
            return None, flag, "called_back"

    return adv, None, None
