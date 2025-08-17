from typing import Dict, Tuple, Optional

ACTION_MATRIX: Dict[Tuple[Optional[str], Optional[str]], str] = {
    # --- Starts / restarts (open-play entry) ---
    (None,     "idle"):         "reastart.kick_off",
    ("dead",   "idle"):         "restart.22Drop",
    ("idle",   "kicked"):       "open_play.kick_chase",   # e.g., 22 drop-out / restart kick

    # --- Kicking flows ---
    ("kicked", "caught"):       "in_play.kick_return",
    ("kicked", "dropped"):      "in_play.scramble",
    ("caught", "kicked"):       "in_play.kick_chase",
    ("dropped","kicked"):       "in_play.kick_chase",

    # --- Carry / contact / offload flows ---
    ("caught",       "in_a_tackle"):  "in_play.tackle",
    ("in_a_tackle",  "offloaded"):    "in_play.offload",
    ("in_a_tackle",  "dropped"):      "in_play.scamble",
    ("in_a_tackle",  "caught"):       "in_play.tackle_complete",   # retained after contact
    ("offloaded",    "caught"):       "in_play.offload_complete",
    ("offloaded",    "dropped"):      "in_play.scramble",

    # --- Loose ball recoveries ---
    ("dropped", "caught"):       "in_play.turnover",
    ("dropped", "dropped"):      "in_play.scramble",      # remains loose between frames

    # --- Touch / out-of-play (kept for analytics; also covered by global override) ---
    ("_",  "in_touch"):     "lineout.start",


    # --- Grounding (also covered by global override) ---
    ("_",  "grounded"):         "score.check_try",
 
}