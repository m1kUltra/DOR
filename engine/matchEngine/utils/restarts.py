# utils/restarts.py
def map_event_to_flag(event: dict) -> dict | None:
    """
    Returns one of:
      {"pending_scrum": {...}} |
      {"pending_lineout": {...}} |
      {"pending_restart": {...}} |
      {"pending_penalty": {...}} |
      None
    """
    etype = event.get("type")
    if etype == "knock_on":
        x = float(event.get("x")); y = float(event.get("y"))
        infringer = event.get("team")  # "a" or "b"
        to = 'a' if infringer == 'b' else 'b'
        return {"pending_scrum": {"x": x, "y": y, "put_in": to, "reason": "knock_on"}}

    if etype == "dead_in_goal":
        to = event.get("to") or event.get("team_last_defending") or 'b'
        return {"pending_restart": {"type": "22_do", "to": to}}

    if etype == "goal_line_do":
        to = event.get("to") or 'b'
        return {"pending_restart": {"type": "goal_line_do", "to": to}}

    if etype == "start_2h":
        to = event.get("to") or 'b'
        return {"pending_restart": {"type": "kickoff", "to": to}}

    # …add touch/50:22 later
    return None


def map_law_event_to_restart(ev):
    t = ev.get("type")
    if t == "into_touch":
        return {"type":"lineout", "to": ev.get("to"), "x":ev.get("x"), "y":ev.get("y")}
    if t == "into_touch_50_22":
        return {"type":"lineout", "to": ev.get("to"), "x":ev.get("x"), "y":ev.get("y")}
    if t == "knock_on":
        to = "a" if ev.get("team")=="b" else "b"
        return {"type":"scrum", "to": to}
    if t == "goal_line_do":
        return {"type":"goal_line_do", "to": ev.get("to")}
    if t == "penalty":
        return {"type":"penalty", "to": ev.get("to"), "mark": ev.get("mark")}
    return None
