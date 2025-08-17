import sqlite3
import json
from player import Player
from team import Team
from ball import Ball
from pitch import Pitch

from utils.db.db_loader import load_team_from_db  # Move load_team_from_db to utils/db_loader.py

def setup_match(db_path, team_a_id, team_b_id):
    # Load raw player dicts (sn, rn, attributes, etc.) from DB
    team_a_name, raw_a_players = load_team_from_db(db_path, team_a_id)
    team_b_name, raw_b_players = load_team_from_db(db_path, team_b_id)

    players = []
    team_a_players = []
    team_b_players = []

    for p in raw_a_players:
        player = Player(
            name=p["name"],
            sn=p["sn"],
            rn=p["rn"],
            team_code="a",
            location=[50.0, 35.0, 0.0],
            attributes=p["attributes"],
            height=p["height"],
            weight=p["weight"]
        )
        players.append(player)
        team_a_players.append(player)

    for p in raw_b_players:
        player = Player(
            name=p["name"],
            sn=p["sn"],
            rn=p["rn"],
            team_code="b",
            location=[100.0, 35.0, 0.0],
            attributes=p["attributes"],
            height=p["height"],
            weight=p["weight"]
        )
        players.append(player)
        team_b_players.append(player)

# matchEngine/setup.py (only the bottom section changes)

    team_a = Team(name=team_a_name, squad=team_a_players, tactics={"attack_dir": +1.0})
    team_b = Team(name=team_b_name, squad=team_b_players, tactics={"attack_dir": -1.0})


    ball = Ball(location=(50.0, 35.0, 0.0), holder=None)
    pitch = Pitch()

    return team_a, team_b, players, ball, pitch


