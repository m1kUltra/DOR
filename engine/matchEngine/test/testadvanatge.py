import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "engine" / "matchEngine"
sys.path.append(str(ROOT))

from utils.laws import advantage
from ball import Ball


def test_possession_flip_releases_ball_and_sets_flag():
    ball = Ball(location=(15.0, 25.0, 2.0), holder="9b")
    adv = advantage.start(
        None,
        type_="knock_on",
        to="a",
        start_x=30.0,
        start_y=40.0,
        start_t=0.0,
        reason="knock_on",
    )

    adv, flag, outcome = advantage.tick(
        adv,
        match_time=1.0,
        ball_x=ball.location[0],
        attack_dir=1.0,
        ball=ball,
        holder_team="b",
    )

    assert adv is None
    assert outcome == "called_back"
    assert ball.holder is None
    assert ball.location == (30.0, 40.0, 2.0)
    assert ball.action == "scrum"
    assert flag and "pending_scrum" in flag