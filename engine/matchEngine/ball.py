# matchEngine/ball.py

import math

class Ball:
    """
    Minimal ball model driven by actions & simple transit profiles.

    Fields you asked for:
      - holder: "10a" or None
      - location: (x, y, z)
      - target: (x, y, z) or None
      - has_bounced: bool (set when hits ground while unheld in open_play; reset when held)
      - transit: dict describing movement from location -> target (parabola / linear / skid / none)
      - action: "passed" | "caught" | "kicked" | None  (last thing that happened to the ball)
      - status / last_status: small wrapper {action, holder, location}; only updates when action changes
    """

    # --- defaults for simple movement/bounce ---
    DEFAULT_HANG_TIME = 1.8    # seconds for a typical kick arc (tweak by action)
    DEFAULT_APEX_H     = 8.0   # meters apex for a hanging kick (tweak per action)
    DEFAULT_SPEED      = 12.0  # m/s for linear moves (passes, quick drags)
    SKID_FRICTION      = 8.0   # m/s^2 deceleration on grass
    SKID_STOP_SPEED    = 0.8   # below this, stop skidding
    BOUNCE_SPEED_KEEP  = 0.55  # how much horizontal speed remains after bounce

    def __init__(self, location=(50.0, 35.0, 0.0), holder=None):
        self.location: tuple[float,float,float] = tuple(map(float, location))
        self.holder: str | None = holder
        self.target: tuple[float,float,float] | None = None
       
        self.has_bounced: bool = False

        # transit is a dict:
        #   {"type":"parabola","t":0.0,"T":..., "start":(x,y,z), "target":(x,y,z), "H":..., "gamma":...}
        #   {"type":"linear","speed":..., "target":(x,y,z)}
        #   {"type":"skid","vx":...,"vy":...}
        # or None (no motion while unheld)
        self.transit: dict | None = None

        # action + status wrapper
        self.action: str | None = None
        self._last_action: str | None = None
        self.status: dict | None = None
        self.last_status: dict | None = None

    # -----------------------
    # basic holder helpers
    # -----------------------
    def is_held(self) -> bool:
        return self.holder is not None

    def release(self) -> None:
        self.holder = None

    # -----------------------
    # status wrapper handling
    # -----------------------
    def _commit_status_if_action_changed(self):
        if self.action != self._last_action:
            self.last_status = self.status
            self.status = {
                "action": self.action,
                "holder": self.holder,
                "location": self.location,
            }
            self._last_action = self.action

    def set_action(self, action: str | None) -> None:
        self.action = action
        print(action,self.holder)
        self._commit_status_if_action_changed()

    # -----------------------
    # transit setters (called by actions)
    # -----------------------
    def set_target(self, xyz: tuple[float,float,float] | None) -> None:
        self.target = xyz

    def start_parabola_to(self, target_xyz: tuple[float,float,float], *,
                          T: float | None = None, H: float | None = None, gamma: float = 1.0) -> None:
        """Start a controlled arc (used by kicks/punted passes)."""
        T = float(T if T is not None else self.DEFAULT_HANG_TIME)
        H = float(H if H is not None else self.DEFAULT_APEX_H)
        self.transit = {
            "type": "parabola",
            "t": 0.0,
            "T": max(1e-3, T),
            "start": self.location,
            "target": tuple(target_xyz),
            "H": max(0.0, H),
            "gamma": max(1e-3, float(gamma)),
        }
        self.set_target(target_xyz)

    def start_linear_to(self, target_xyz: tuple[float,float,float], *, speed: float | None = None) -> None:
        """Simple straight move at constant planar speed (used by quick drags/short passes if you want)."""
        self.transit = {
            "type": "linear",
            "speed": float(speed if speed is not None else self.DEFAULT_SPEED),
            "target": tuple(target_xyz),
        }
        self.set_target(target_xyz)

    def start_skid(self, vx: float, vy: float) -> None:
        """Ground skid after bounce."""
        self.transit = {"type": "skid", "vx": float(vx), "vy": float(vy)}
        # keep target as-is; skid is free-rolling

    # -----------------------
    # update per-tick
    # -----------------------
    def update(self, match) -> None:
        """
        If held: snap to holder; clear transit; reset bounce.
        If unheld: advance transit; detect bounce (only in open_play); possibly start skid; otherwise stop on arrival.
        """
        dt = float(getattr(match, "tick_rate", 0.05))

        # 1) held: follow player, clear motion & bounce flags
        if self.is_held():
            try:
                sn = int(self.holder[:-1])
                team_code = self.holder[-1]
                team = match.team_a if team_code == "a" else match.team_b
                p = team.get_player_by_sn(sn)
                if p:
                    self.location = p.location
            except Exception:
                # if parsing fails, just keep location
                pass
            # when held, we consider motion authored by the carrier; clear any transit and reset bounce flag
            self.transit = None
            self.has_bounced = False
            # status wrapper still only changes when action changes via set_action()
            return

        # 2) unheld: advance transit if any
        if not self.transit:
            return

        ttype = self.transit.get("type")

        if ttype == "parabola":
            # parametric dome: z(s) = H * 4 * s'(1 - s'), with time skew s' = s^gamma
            self.transit["t"] += dt
            T   = self.transit["T"]
            s   = min(1.0, max(0.0, self.transit["t"] / T))
            gma = self.transit["gamma"]
            s2  = s ** gma

            x0, y0, z0 = self.transit["start"]
            xt, yt, zt = self.transit["target"]
            # straight-line planar interpolation
            x = x0 + (xt - x0) * s
            y = y0 + (yt - y0) * s
            # dome height
            H  = self.transit["H"]
            z  = max(0.0, H * 4.0 * s2 * (1.0 - s2))  # clamps to ground

            self.location = (x, y, z)

            # landing
            if s >= 1.0:
                # hit ground
                on_open_play = getattr(getattr(match, "current_state", None), "name", "") == "open_play"
                if on_open_play:
                    self.has_bounced = True
                # compute simple landing planar velocity from last small step (for skid)
                eps = 1e-3
                prev_s = max(0.0, 1.0 - eps)
                prev_s2 = prev_s ** gma
                x_prev = x0 + (xt - x0) * prev_s
                y_prev = y0 + (yt - y0) * prev_s
                vx = (x - x_prev) / max(eps * T, 1e-6)
                vy = (y - y_prev) / max(eps * T, 1e-6)
                vx *= self.BOUNCE_SPEED_KEEP
                vy *= self.BOUNCE_SPEED_KEEP

                # start skid after bounce
                self.location = (xt, yt, 0.0)
                self.start_skid(vx, vy)

        elif ttype == "linear":
            x, y, z = self.location
            xt, yt, zt = self.transit["target"]
            spd = max(0.0, float(self.transit["speed"]))
            dx, dy, dz = (xt - x), (yt - y), (zt - z)
            d2 = dx*dx + dy*dy + dz*dz
            if d2 <= (spd * dt) ** 2:
                self.location = (xt, yt, zt)
                self.transit = None
            else:
                k = (spd * dt) / math.sqrt(d2)
                self.location = (x + dx * k, y + dy * k, z + dz * k)

        elif ttype == "skid":
            x, y, z = self.location
            vx = float(self.transit.get("vx", 0.0))
            vy = float(self.transit.get("vy", 0.0))

            # decelerate by friction
            speed = math.hypot(vx, vy)
            if speed <= self.SKID_STOP_SPEED:
                self.transit = None
                # remain where it stopped (z already 0 in practice)
                self.location = (x, y, 0.0)
            else:
                # apply friction opposite velocity
                ax = -vx / max(speed, 1e-6) * self.SKID_FRICTION
                ay = -vy / max(speed, 1e-6) * self.SKID_FRICTION
                vx2 = vx + ax * dt
                vy2 = vy + ay * dt

                # move
                x2 = x + vx2 * dt
                y2 = y + vy2 * dt
                self.location = (x2, y2, 0.0)
                self.transit["vx"] = vx2
                self.transit["vy"] = vy2

        else:
            # unknown transit -> stop
            self.transit = None
      
        # keep status wrapper consistent (but only changes when action changed externally)
        self._commit_status_if_action_changed()

"""
ball overhaul. first  keep alot of the same logic but its physics can go aside from bouncing - i dont understand therefore fine
ball should have:
holder (player or none)
location (x,y,z)
target (x,y,z)
has_bounced - hit gound while holder == none & state == open_play reset when holder != none 
transit(type of movement it will do to get from loaction to target- this is where all physics and speed should be dealt with)
this takes the infor coming from actions and probs and enacts them on the ball  
action (what has most recently happened to ball) passed, caught, kicked 
note status is only run if action != prev.action
status wrap (action, holder, location)
last_status (save previous action before overwrite)
"""
"""add in idle status, does not tell controller.status but held locally"""
"""
the following are things that the ball.status can be
caught , kicked , in_a_tackle, offloaded, dead, idle, in_touch, grounded, dropped


"""