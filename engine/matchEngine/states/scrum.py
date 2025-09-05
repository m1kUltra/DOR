
# states/scrum.py
from typing import Optional
import random, event  # your project's event system

# Public tags
CROUCH = "scrum.crouch"
BIND   = "scrum.bind"
SET    = "scrum.set"
FEED   = "scrum.feed"
DRIVE  = "scrum.drive"
STABLE = "scrum.stable"
OUT    = "scrum.out"

SCRUM_TAGS = {CROUCH, BIND, SET, FEED, DRIVE, STABLE, OUT}

# Handlers are implemented in set_pieces.scrum
from set_pieces.scrum import (
    handle_crouch, handle_bind, handle_set,
    handle_feed, handle_drive, handle_stable, handle_out
)

def maybe_handle(match, tag, loc, ctx) -> bool:
    """Dispatch scrum states using the same style as states/ruck.py."""
    if not isinstance(tag, str) or not (tag == CROUCH or tag.startswith("scrum.")):
        return False

    if tag == CROUCH:
        handle_crouch(match, (tag, loc, ctx)); return True
    if tag == BIND:
        handle_bind(match, (tag, loc, ctx));   return True
    if tag == SET:
        handle_set(match, (tag, loc, ctx));    return True
    if tag == FEED:
        handle_feed(match, (tag, loc, ctx));   return True
    if tag == DRIVE:
        handle_drive(match, (tag, loc, ctx));  return True
    if tag == STABLE:
        handle_stable(match, (tag, loc, ctx)); return True
    if tag == OUT:
        handle_out(match, (tag, loc, ctx));    return True

    return False
