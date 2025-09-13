# states/lineout.py — flags only
# states/lineout.py
from typing import Optional


START   = "lineout.start"
FORMING = "lineout.forming"
OVER    = "lineout.over"
OUT     = "lineout.out"

LINEOUT_TAGS = {START, FORMING, OVER, OUT}

from set_pieces.lineout import handle_start, handle_forming, handle_over, handle_out

def maybe_handle(match, tag, loc, ctx) -> bool:
    if not isinstance(tag, str) or not (tag == START or tag.startswith("lineout.")):
        return False

    if tag == START:
        handle_start(match, (tag, loc, ctx))
        match.lineout_roles = handle_start(match, (tag, loc, ctx))
        return True
    if tag == FORMING:
        codes = getattr(match, "lineout_roles", None)
        handle_forming(match, codes, (tag, loc, ctx))
        if hasattr(match, "lineout_roles"):
            delattr(match, "lineout_roles")
        return True
    if tag == OVER:
        handle_over(match, (tag, loc, ctx))
        return True
    if tag == OUT:
        handle_out(match, (tag, loc, ctx))
        return True
    return False