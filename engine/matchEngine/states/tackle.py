"""
as well as an action a tackle is a state. 
players have new options unavcailable else where based on outcome of tackle
can leg-drive offload or attempt to score 

"""
# states/tackle.py — flags only

START            = "tackle.start"
TACKLE_COMPLETE  = "in_play.tackle_complete"   # included because your matrix uses this exact tag

TACKLE_TAGS = {
    START,
    TACKLE_COMPLETE,
}
