import sys
from pathlib import Path

import pytest
from unittest.mock import patch

# The "team" package lives under engine/matchEngine in this repository.
sys.path.append(str(Path(__file__).resolve().parents[1] / "engine" / "matchEngine"))

from engine.matchEngine.choice.scrum.common import (
    ScrumScore,
    compute_stage_1,
    compute_stage_2,
    compute_stage_3,
    compute_drive_increment,
    outcome_from_score,
)
from engine.matchEngine.choice.scrum import drive as drive_plan


class DummyPlayer:
    def __init__(self, rn, team_code, norm=None, weight=0.0, attrs=None):
        self.rn = rn
        self.team_code = team_code
        self.norm_attributes = norm or {}
        self.weight = weight
        self.attributes = attrs or {}
        self.pid = f"{rn}{team_code}"
        self.code = self.pid
        self.phase_role = "scrum"


class DummyTeam:
    def __init__(self, players):
        self._players = players

    def get_player_by_rn(self, rn):
        return self._players.get(rn)


class DummyBall:
    def __init__(self):
        self.location = (0.0, 0.0, 0.0)
        self.actions = []

    def set_action(self, action):
        self.actions.append(action)


class DummyMatch:
    def __init__(self, team_a, team_b):
        self.team_a = team_a
        self.team_b = team_b
        self.possession = "a"
        self.ball = DummyBall()
        self.players = list(team_a._players.values()) + list(team_b._players.values())
        self.scrum_tactic = "mixed"


# --- compute stage tests -------------------------------------------------

def test_compute_stage1_and_outcome():
    a_players = {
        1: DummyPlayer(1, "a", norm={"scrummaging": 1}),
        2: DummyPlayer(2, "a", norm={"leadership": 1}),
        3: DummyPlayer(3, "a", norm={"scrummaging": 1}),
    }
    b_players = {1: DummyPlayer(1, "b"), 2: DummyPlayer(2, "b"), 3: DummyPlayer(3, "b")}
    match = DummyMatch(DummyTeam(a_players), DummyTeam(b_players))

    s = ScrumScore()
    compute_stage_1(match, "a", s)

    assert pytest.approx(s.value, rel=1e-6) == 0.5 + (1 ** 2) * (1 + 1) / 3
    assert outcome_from_score(s.value) == "pen_feed"

def test_compute_stage2():
    a_players = {
        1: DummyPlayer(1, "a", norm={"scrummaging": 1, "strength": 2}),
        2: DummyPlayer(2, "a"),
        3: DummyPlayer(3, "a", norm={"scrummaging": 1, "strength": 2}),
    }
    b_players = {1: DummyPlayer(1, "b"), 2: DummyPlayer(2, "b"), 3: DummyPlayer(3, "b")}
    match = DummyMatch(DummyTeam(a_players), DummyTeam(b_players))

    s = ScrumScore()
    compute_stage_2(match, "a", s)

    assert pytest.approx(s.value, rel=1e-6) == 0.5 + (1 * 2 * 1 * 2)


def test_compute_stage3_and_penalty():
    a_players = {j: DummyPlayer(j, "a", norm={}) for j in range(1, 8)}
    b_players = {j: DummyPlayer(j, "b", norm={}) for j in range(1, 8)}
    # add weight and scrummaging for props in team A
    a_players[1].weight = a_players[3].weight = 100
    for j in range(2, 8):
        a_players[j].weight = 100
    a_players[1].norm_attributes["scrummaging"] = 1
    a_players[3].norm_attributes["scrummaging"] = 1

    match = DummyMatch(DummyTeam(a_players), DummyTeam(b_players))

    s = ScrumScore()
    with patch("engine.matchEngine.choice.scrum.common.random.random", side_effect=[1.0, 0.0, 0.0, 0.0]):
        compute_stage_3(match, "a", s)

    assert pytest.approx(s.value, rel=1e-6) == 0.5 + (700 / 1000) * 2 * 1.0
    assert outcome_from_score(s.value) == "pen_feed"


# --- drive increment -----------------------------------------------------

def test_compute_drive_increment():
    a_players = {
        1: DummyPlayer(1, "a", norm={"scrummaging": 1, "strength": 1, "aggression": 1}),
        2: DummyPlayer(2, "a", norm={"scrummaging": 1, "strength": 1, "aggression": 1}),
        3: DummyPlayer(3, "a", norm={"scrummaging": 1, "strength": 1, "aggression": 1}),
        4: DummyPlayer(4, "a", norm={"determination": 1, "strength": 1}),
        5: DummyPlayer(5, "a", norm={"determination": 1, "strength": 1}),
    }
    b_players = {j: DummyPlayer(j, "b") for j in range(1, 6)}
    match = DummyMatch(DummyTeam(a_players), DummyTeam(b_players))

    inc = compute_drive_increment(match, "a")
    assert pytest.approx(inc, rel=1e-6) == 1.0


# --- drive plan drift check ----------------------------------------------

def test_drive_plan_push_when_score_high():
    a_players = {
        1: DummyPlayer(1, "a", norm={"scrummaging": 1, "strength": 0, "aggression": 0}),
        2: DummyPlayer(2, "a", norm={"leadership": 0.5}),
        3: DummyPlayer(3, "a", norm={"scrummaging": 1, "strength": 0, "aggression": 0}),
        4: DummyPlayer(4, "a"),
        5: DummyPlayer(5, "a"),
    }
    b_players = {j: DummyPlayer(j, "b") for j in range(1, 6)}
    match = DummyMatch(DummyTeam(a_players), DummyTeam(b_players))

    s = ScrumScore()
    compute_stage_1(match, "a", s)
    match._scrum_score = s

    calls = drive_plan.plan(match, None)
    assert calls and all(action[0] == "push" for _, action, _, _ in calls)