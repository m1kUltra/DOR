from typing import Dict, Tuple, Optional

# Sentinel used to indicate “no state change”
SAME: str = "__SAME__"

ACTION_MATRIX: Dict[Tuple[Optional[str], Optional[str]], str] = {
    # --- Starts / restarts (open-play entry) ---
    (None,     "idle"):         "restart.kick_off",
    ("dead",   "idle"):         "restart.22Drop",
    ("idle",   "kicked"):       "open_play.kick_chase",
    ("goal_line", "idle"):      "restart.goal_line_drop",
    ("_", "goal_line"):      "restart.goal_line_drop",   # e.g., 22 drop-out / restart kick
    ("conversion", "idle") :     "restart.kick_off",
    # --- Global wildcards ---
    ("_", "kicked"):            "open_play.kick_chase",   # ⬅️ any -> kicked
    ("_", "passed"):            SAME,                     # ⬅️ any -> passed (no state change)
    ("_", "caught"):            "open_play.joue",
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
    ("grounded", "dropped"):    'open_play.scramble',

    # --- Touch / out-of-play ---
    ("_",  "in_touch"):          "lineout.start",

    # --- Grounding ---
    ("_",  "grounded"):          "score.check_try",
    ("grounded", "in_a_tackle"): "score.check_try",
    ("_", "try"):        "nudge.conversion",
    ("_", "conversion"):         "nudge.after_conversion",

   #tackle 
   
    ("_", "tackled"):       "ruck.start",         # a
    ("_", "ruck_forming"):  "ruck.forming",
    ("_", "ruck_over"):     "ruck.over",  
    ("_", "picked"): "ruck.out",
    ("picked", "_"): "open_play.phase_play", 
    # Remove or narrow: ("_", "passed"): SAME
    ("picked", "passed"): "open_play.phase_play",
    ("passed", "pass_error"):  "open_play.scramble",
    ("_",      "pass_error"):  "open_play.scramble",
    


("_",        "line_break"): "open_play.line_break", # safety


("_",        "turnover"):   "open_play.turnover", 


    # --- existing mappings above ---

    # --- Penalty & scrum call‑backs ---
    ("_", "penalty"):            "nudge.quick_tap",      # route into penalty‑option handler

   # Scrum progression driven by ball actions
    ("_", "scrum"):       "scrum.start",
      ("_", "scrum.crouch"):       "scrum.crouch",
    ("_", "scrum.bind"):         "scrum.bind",
    ("_", "scrum.set"):          "scrum.set",
    ("scrum.set", "feed"):         "scrum.feed",
    ("_", "hook"):        "scrum.drive",
    ("_", "scrum.stable"):       "scrum.stable",
    ("_", "scrum.out"):         "scrum.out",
    ("scrum.stable", "picked"): "scrum.out",
    ("scrum.out", "passed"): "open_play.phase_play",
    ("scrum.out", "_"): "open_play.phase_play",
    ("picked", "_"): "open_play.phase_play",
          # ball released from the scrum

    # --- Line‑out sequence ---
    ("_", "lineout_forming"):        "lineout.forming",
    ("lineout_forming", "lineout_over"): "lineout.over",
    ("lineout_over", "_"):           "lineout.out",   
       
    ("in_a_tackle", "tackle_broken"): SAME,
    ("_", "passive_tackle"): "ruck.start",
    ("_", "dominant_tackle"): "ruck.start",
    ("_", "murder"): "ruck.start",
       # throw contest resolved

    # --- existing mappings below ---


      #


}
