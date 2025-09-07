# matchEngine/constants.py

# ------------------------------------------------------------------------------
# Core Pitch Dimensions (in meters)
# ------------------------------------------------------------------------------

PITCH_LENGTH = 100.0  # Tryline to tryline
PITCH_WIDTH = 70.0    # Sideline to sideline
DEADBALL_BUFFER = 15.0  # Extra area behind trylines

FULL_PITCH_LENGTH = PITCH_LENGTH + 2 * DEADBALL_BUFFER  # 120m total
FULL_PITCH_WIDTH = PITCH_WIDTH  # Width remains 70m

# ------------------------------------------------------------------------------
# Boundaries
# ------------------------------------------------------------------------------

TRYLINE_A_X = 0.0
TRYLINE_B_X = 100.0
DEADBALL_LINE_A_X = -15.0
DEADBALL_LINE_B_X = 115.0

TOUCHLINE_TOP_Y = 70.0
TOUCHLINE_BOTTOM_Y = 0.0

Twenty2_A_X= 22
Twenty2_B_X= 78
The10_A_X=40
The10_B_X = 60
The5_A_X=5
The5_B_X = 95

Tram5_Top_Y = 65
Tram5_Bottom_Y = 5
Tram15_Top_Y = 55
Tram15_Bottom_Y = 15


# ------------------------------------------------------------------------------
# Gameplay Constants
# ------------------------------------------------------------------------------

DEFAULT_PLAYER_SPEED = 5.0  # m/s
DEFAULT_BALL_SPEED = 15.0  # m/s
TACKLE_RANGE = 2.0         # m
PASS_SUCCESS_RATE = 1.0    # Always successful for now

# ------------------------------------------------------------------------------
# Coordinate Reference System
# ------------------------------------------------------------------------------
EPS = 1e-6
# Z-axis: vertical (for jumping/kicking height)
# (x, y, z): where x = length, y = width, z = height

ORIGIN = (0.0, 0.0, 0.0)  # Bottom-left corner of in-play area
 
 # Role Groups
FORWARDS = {1, 2, 3, 4, 5, 6, 7, 8}
BACKS = {9, 10, 11, 12, 13, 14, 15}
MAX_PASS_CANDIDATES = 6

MAX_DEF_CONSIDERED = 7

MAX_RUCK_COMMIT_SCAN = 6 #(per side)

MAX_RECEIVE_CONTESTERS = 5 #(for kicks)
PASS_MAX_RANGE = 14.0
RUN_PROBE_LEN = 10.0
DEF_MIN_LAT_GAP = 3.0
LINE_DEPTH = 1.5
MAX_CHASERS = 5
CROSSFIELD_MIN_SPACE = 12.0

TACKLE_TRIGGER_DIST = 1.8
TACKLER_DOWN_TICKS = 2

RUCK_RADIUS = 3.0
RUCK_GATE_WIDTH = 2.5
GATE_DEPTH = 0.5

RUCK_FORM_TICKS = 2
RUCK_CONTEST_TICKS = 2
RECYCLE_FAST_TICKS = 2
RECYCLE_SLOW_TICKS = 4

OFFSIDE_PENALTY_ENFORCE = True

# === Phase 5: Kicking polish & restarts ===
# Base ball speed (scaled by attributes later)
KICK_BASE_V0 = 18.0     # m/s typical open-play long kick

# Preset scalars (multiply base)


# Small physics polish
AIR_DRAG_COEFF = 0.02       # mild vertical slow, applied to vz
LATERAL_DRIFT_MAX = 0.20    # cap on vy/v0 fraction after all hints
CATCH_RADIUS = 1.8          # m (hands reach + jump window later)
CATCH_EARLY_S = 0.15        # can't catch before this after bounce/apex arrival
CATCH_LAND_SLOP = 0.25      # still catchable near ground within this time
BOUNCE_ENERGY_GRUBBER = 0.45 # vx damp when z<=0 for grubbers
BOUNCE_ENERGY_DEFAULT = 0.60 # other types

# Kickoff/dropout placements
KICKOFF_SPREAD_GAP_Y = 4.0
DROP_OUT_MIN = 10.0         # m (typical law realism, keep simple)
DROP_OUT_MAX = 35.0


# === Phase 6: Laws & Scoring v1 ===
# Laws
FORWARD_PASS_EPS = 0.05          # meters tolerance
KNOCK_ON_FORWARD_METERS = 0.2    # minimum forward displacement on bobble
OFFSIDE_OPENPLAY_BUFFER = 1.0     # meters behind last feet / last kick point

# Scoring
POINTS = {"try": 5, "conv": 2, "pen": 3, "dg": 3}

CONVERSION_WINDOW_S = 45.0       # time allowed to attempt kick at goal
CONVERSION_SPOT_OFFSET_X = 0.0   # x is try spot; ball placed on y of try
CONVERSION_DEFAULT_DIST = 25.0   # meters back from try line (fallback if you want)
CONV_SUCCESS_BASE = 0.75         # Phase 6 simple success (attributes later)

# 50:22
FIFTY22_MIN_ORIGIN = 50.0        # must kick from own half
FIFTY22_TARGET_MINX = 78.0       # must go out past opponent 22 via bounce

POST_GAP = 2.5
CROSSBAR = 3.0
GameSpeed =100