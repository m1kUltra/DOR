# states/scrum.py — flags only
# states/scrum.py
from typing import Optional


START   = "scrum.start"
FORMING = "scrum.forming"
OVER    = "scrum.over"
OUT     = "scrum.out"

SCRUM_TAGS = {START, FORMING, OVER, OUT}

from set_pieces.scrum import handle_start, handle_forming, handle_over, handle_out

def maybe_handle(match, tag, loc, ctx) -> bool:
    if not isinstance(tag, str) or not (tag == START or tag.startswith("scrum.")):
        return False

    if tag == START:
        handle_start(match, (tag, loc, ctx))
        return True
    if tag == FORMING:
        handle_forming(match, (tag, loc, ctx))
        return True
    if tag == OVER:
        handle_over(match, (tag, loc, ctx))
        return True
    if tag == OUT:
        handle_out(match, (tag, loc, ctx))
        return True
    return False