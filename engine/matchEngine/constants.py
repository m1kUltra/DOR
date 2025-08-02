# matchEngine/constants.py

# ------------------------------------------------------------------------------
# Core Pitch Dimensions (in meters)
# ------------------------------------------------------------------------------

PITCH_LENGTH = 100.0  # Tryline to tryline
PITCH_WIDTH = 70.0    # Sideline to sideline
DEADBALL_BUFFER = 10.0  # Extra area behind trylines

FULL_PITCH_LENGTH = PITCH_LENGTH + 2 * DEADBALL_BUFFER  # 120m total
FULL_PITCH_WIDTH = PITCH_WIDTH  # Width remains 70m

# ------------------------------------------------------------------------------
# Boundaries
# ------------------------------------------------------------------------------

TRYLINE_A_X = 0.0
TRYLINE_B_X = 100.0
DEADBALL_LINE_A_X = -10.0
DEADBALL_LINE_B_X = 110.0

TOUCHLINE_TOP_Y = 70.0
TOUCHLINE_BOTTOM_Y = 0.0

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

# Z-axis: vertical (for jumping/kicking height)
# (x, y, z): where x = length, y = width, z = height

ORIGIN = (0.0, 0.0, 0.0)  # Bottom-left corner of in-play area
