# states/open_play.py

# flat string constants for open-play substates
LAUNCH_PLAY = "open_play.launch_play"
PHASE_PLAY  = "open_play.phase_play"
KICK_RETURN = "open_play.kick_return"
TURNOVER    = "open_play.turnover"
LINE_BREAK  = "open_play.line_break"
SCRAMBLE = "open_play.scramble"
KICK_CHASE ="open_play.kick_chase"
TACKLE = "open_play.tackle"
JOUE = "open_play.joue"
# handy set if you ever want to check membership
OPEN_PLAY_TAGS = {
    LAUNCH_PLAY,
    PHASE_PLAY,
    KICK_RETURN,
    TURNOVER,
    LINE_BREAK,
    SCRAMBLE,
    KICK_CHASE,
    TACKLE,
    JOUE,
}



"""open play has a few subsections that transition between eachother freely
1. launch_play occurs after scrum_linout and rolling_maul
2. phase_play occurs after a ruck- most common type
3. kick_return occurs after ball_last status was caught and the other team kicked it (need to store who kicked it, location_of_kick)
4. turnover- occurs after interception,non-ruck or scamble 
5. line break- occurs when the ball is held and ahead of min (11) of the opposing team

all of these overwrite eachotrher and can be overwritten by other states
"""