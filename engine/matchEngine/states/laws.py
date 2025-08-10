from utils.logger import log_law

# inside simulate_flight_step or equivalent
if z <= 0.0:
    z = 0.0

    # into touch
    if y <= TOUCHLINE_BOTTOM_Y or y >= TOUCHLINE_TOP_Y:
        clamp_x = max(min(x, DEADBALL_LINE_B_X), DEADBALL_LINE_A_X)
        throw_to = 'b' if getattr(match, "last_touch_team", 'a') == 'a' else 'a'
        match.pending_lineout = {
            "x": clamp_x,
            "y": y,
            "throw_to": throw_to,
            "reason": "touch"
        }
        log_law(match.tick_count, "into_touch",
                {"x": clamp_x, "y": y, "last_touch_by": match.last_touch_team}, match=match)
        self.in_flight = False
        self.velocity = (0.0, 0.0, 0.0)
        return

    # dead in-goal
    if x < DEADBALL_LINE_A_X or x > DEADBALL_LINE_B_X:
        x = max(min(x, DEADBALL_LINE_B_X), DEADBALL_LINE_A_X)
        defending_to = 'b' if getattr(match, "last_touch_team", 'a') == 'a' else 'a'
        match.restart_controller({"type": "dead_in_goal", "to": defending_to})
        log_law(match.tick_count, "dead_in_goal",
                {"x": x, "y": y, "last_attack": match.last_touch_team, "to": defending_to}, match=match)
        self.in_flight = False
        self.velocity = (0.0, 0.0, 0.0)
        self.location = (x, y, z)
        return
