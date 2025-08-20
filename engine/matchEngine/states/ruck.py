# states/ruck.py — flags only
# states/ruck.py

# Entry / setup
START                  = "ruck.start"
FORMING                = "ruck.forming"
TACKLER_ROLL_REQUIRED  = "ruck.tackler_roll_required"
CONTEST_LIVE           = "ruck.contest_live"

# Contest modes
JACKAL                 = "ruck.jackal"
COUNTER_RUCK           = "ruck.counter_ruck"

# Attacking responses
CLEAROUT               = "ruck.clearout"
SHUT_DOWN              = "ruck.shut_down"     # early see-off succeeds

# Outcomes
WON_ATTACK             = "ruck.won_attack"    # retain possession -> phase play
TURNOVER               = "ruck.turnover"      # possession flips
PENALTY                = "ruck.penalty"       # ctx should include the awarded team

RUCK_TAGS = {
    START, FORMING, TACKLER_ROLL_REQUIRED, CONTEST_LIVE,
    JACKAL, COUNTER_RUCK, CLEAROUT, SHUT_DOWN,
    WON_ATTACK, TURNOVER, PENALTY,
}
