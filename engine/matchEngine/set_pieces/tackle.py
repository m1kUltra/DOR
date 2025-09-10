"""Resolve tackle outcomes based on player attributes."""

from utils.probs.scale import balanced_score


def resolve_tackle(match, tackler, carrier):
    """Resolve a tackle between ``tackler`` and ``carrier``.

    Uses a simple balanced score between the carrier's footwork,
    strength and balance against the tackler's tackling, bravery and
    determination.  The resulting score maps to discrete outcomes which
    are written to ``ball.action``.  Basic state flags are reset where
    appropriate.
    """
    c_attrs = getattr(carrier, "norm_attributes", {}) or {}
    t_attrs = getattr(tackler, "norm_attributes", {}) or {}

    footwork = float(c_attrs.get("footwork", 0.0))
    strength = float(c_attrs.get("strength", 0.0))
    balance = float(c_attrs.get("balance", 0.0))

    tackling = float(t_attrs.get("tackling", 0.0))
    bravery = float(t_attrs.get("bravery", 0.0))
    determination = float(t_attrs.get("determination", 0.0))

    att = (footwork * strength * balance) ** (1.0 / 3.0)
    def_ = (tackling * bravery * determination) ** (1.0 / 3.0)

    score = balanced_score(att, def_, exponent=0.5)

    if score > 0.5:
        outcome = "tackle_broken"
    elif score > 0.2:
        outcome = "passive_tackle"
    elif score > -0.2:
        outcome = "tackled"
    elif score > -0.5:
        outcome = "dominant_tackle"
    else:
        outcome = "murder"

    match.ball.set_action(outcome)

    # reset state flags
    tackler.state_flags["tackling"] = False
    if outcome == "tackle_broken":
        carrier.state_flags["being_tackled"] = False