from typing import Dict, Tuple, Optional

# Sentinel used to indicate “no state change”
SAME: str = "__SAME__"

ACTION_MATRIX: Dict[Tuple[Optional[str], Optional[str]], str] = {
    # --- Starts / restarts (open-play entry) ---
    (None,     "idle"):         "restart.kick_off",
    ("dead",   "idle"):         "restart.22Drop",
    ("idle",   "kicked"):       "open_play.kick_chase",   # e.g., 22 drop-out / restart kick
    ("conversion", "idle") :     "restart.kick_off",
    # --- Global wildcards ---
    ("_", "kicked"):            "open_play.kick_chase",   # ⬅️ any -> kicked
    ("_", "passed"):            SAME,                     # ⬅️ any -> passed (no state change)

    # --- Kicking flows (kept; exact beats wildcard, both resolve to kick_chase anyway) ---
    ("kicked", "caught"):       "open_play.kick_return",
    ("kicked", "dropped"):      "open_play.scramble",
    ("caught", "kicked"):       "open_play.kick_chase",
    ("dropped","kicked"):       "open_play.kick_chase",

    # --- Carry / contact / offload flows ---
    ("caught",       "in_a_tackle"):  "open_play.tackle",
    ("in_a_tackle",  "offload"):    SAME,
    ("in_a_tackle",  "dropped"):      "open_play.scramble",
    ("in_a_tackle",  "caught"):       "open_play.tackle_complete",
    ("offload",    "caught"):       "open_play.joue",
    ("offload",    "dropped"):      "open_play.scramble",

    # --- Loose ball recoveries ---
    ("dropped", "caught"):       "open_play.turnover",
    ("dropped", "dropped"):      "open_play.scramble",

    # --- Touch / out-of-play ---
    ("_",  "in_touch"):          "lineout.start",

    # --- Grounding ---
    ("_",  "grounded"):          "score.check_try",
    ("grounded", "try"):        "nudge.conversion",
    ("_", "conversion"):         "nudge.after_conversion",

   #tackle 
   
    ("_", "tackled"):       "ruck.start",         # a
    ("_", "ruck_forming"):  "ruck.forming",
    ("_", "ruck_over"):     "ruck.over",          #


}
