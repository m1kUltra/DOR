import math
from constants import AIR_DRAG_COEFF, LATERAL_DRIFT_MAX, BOUNCE_ENERGY_GRUBBER, BOUNCE_ENERGY_DEFAULT
# matchEngine/ball.py
from constants import (
    DEADBALL_LINE_A_X, DEADBALL_LINE_B_X,
    TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y,
)

class Ball:
    def __init__(self, location=(0.0, 0.0, 0.0), holder=None):
        """
        location: (x, y, z) in meters
        holder: '15a' (sn+team_code) or None
        """
        self.location = location
        self.holder = holder
        # flight state
        self.velocity = (0.0, 0.0, 0.0)  # (vx, vy, vz) m/s
        self.in_flight = False           # True when kicked

    def is_held(self):
        return self.holder is not None

    def release(self):
        self.holder = None

    def _update_flight(self, match):
        if not self.in_flight:
            return

        x, y, z = self.location
        vx, vy, vz = self.velocity
        dt = match.tick_rate

        # integrate
        g = 9.81  # m/s^2
        x += vx * dt
        y += vy * dt
        z += vz * dt
        vz -= g * dt
        # air drag
        vz -= AIR_DRAG_COEFF * vz * dt

        # lateral drift shaping
        v_plane = math.sqrt(vx*vx + vy*vy)
        if v_plane > 1e-6:
            max_lat = LATERAL_DRIFT_MAX * v_plane
            if abs(vy) > max_lat:
                vy = max(-max_lat, min(max_lat, vy))
        # ground contact
        if z <= 0.0:
            z = 0.0
            # mark first bounce for 50:22
            try:
                _phase6_mark_bounce(match)
            except Exception:
                pass
            # check touch/deadball before bounce
            if y <= TOUCHLINE_BOTTOM_Y or y >= TOUCHLINE_TOP_Y:
                # into touch: lineout at cross point
                match.pending_lineout = {
                    "x": max(min(x, DEADBALL_LINE_B_X), DEADBALL_LINE_A_X),
                    "y": y,
                    # throw to opposite of last touch (set by kicker)
                    "throw_to": 'b' if getattr(match, "last_touch_team", 'a') == 'a' else 'a'
                }
                self.in_flight = False
                self.velocity = (0.0, 0.0, 0.0)
                return

            # dead in-goal (beyond deadball lines) – simplify: stop where it landed
            if x < DEADBALL_LINE_A_X or x > DEADBALL_LINE_B_X:
                x = max(min(x, DEADBALL_LINE_B_X), DEADBALL_LINE_A_X)
                self.in_flight = False
                self.velocity = (0.0, 0.0, 0.0)
                self.location = (x, y, z)
                return

            # simple bounce: lose energy, low random skid off y kept
            try:
                self._on_ground_contact()
            except Exception:
                pass
            vz = 0.0
            vx *= 0.6
            vy *= 0.6
            # stop if very slow
            if abs(vx) < 0.5 and abs(vy) < 0.5:
                self.in_flight = False
                vx = vy = vz = 0.0

        self.location = (x, y, z)
        self.velocity = (vx, vy, vz)

    def update(self, match):
        """
        Called every tick from Match.update().
        If held, lock position to the holder's player; else update flight.
        """
        if self.holder:
            sn = int(self.holder[:-1])
            team_code = self.holder[-1]
            team = match.team_a if team_code == 'a' else match.team_b
            player = team.get_player_by_sn(sn)
            if player:
                self.location = player.location
                # when held, it's not in flight
                self.in_flight = False
                self.velocity = (0.0, 0.0, 0.0)
            return

        # loose or kicked
        self._update_flight(match)


def _on_ground_contact(self):
    prof = self.flight_profile or {}
    ktype = prof.get("type")
    if ktype == "grubber":
        vx, vy, vz = self.velocity
        self.velocity = (vx * BOUNCE_ENERGY_GRUBBER, vy * BOUNCE_ENERGY_GRUBBER, 0.0)
        self.location = (self.location[0], self.location[1], 0.0)
        self.in_flight = True  # continue skidding
    else:
        # default bounce energy (existing behaviour expected elsewhere)
        pass


# Phase 6: mark first bounce for 50:22
def _phase6_mark_bounce(match):
    lk = getattr(match, "last_kick", None)
    if lk and not lk.get("bounced", False):
        lk["bounced"] = True
