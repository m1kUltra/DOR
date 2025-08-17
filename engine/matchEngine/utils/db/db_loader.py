import sqlite3
import json
from utils.player.normalise_player import normalise_attrs
def load_team_from_db(db_path, nation_team_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch team name and squad JSON blob
    cursor.execute(
        "SELECT team_name, squad_json FROM national_teams WHERE nation_team_id = ?",
        (nation_team_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"No team found with ID {nation_team_id}")

    team_name, squad_json = row
    squad_data = json.loads(squad_json or "{}")
    starters = squad_data.get("selection", {}).get("starters", [])

    # Extract squad number (sn) and role number (rn) from selection
    sn_rn_map = [
        {
            "sn": i + 1,
            "rn": player.get("position"),
            "player_id": player.get("player_id")
        }
        for i, player in enumerate(starters)
        if player.get("player_id") and player.get("position")
    ]

    player_ids = [entry["player_id"] for entry in sn_rn_map]
    if not player_ids:
        raise ValueError(f"No valid starters found for team {team_name}")

    # Build query to fetch all relevant player data
    placeholders = ",".join(["?"] * len(player_ids))
    cursor.execute(f"""
        SELECT player_id, firstname, surname, current_ability, height, weight, attributes
        FROM players
        WHERE player_id IN ({placeholders})
    """, player_ids)

    # Map DB records to player_id -> data
    id_to_data = {
        pid: {
            "name": f"{first} {last}",
            "current_ability": ca,
            "height": height,
            "weight": weight,
            "attributes": json.loads(attrs) if attrs else {}
        }
        for pid, first, last, ca, height, weight, attrs in cursor.fetchall()
    }

    conn.close()

    # Combine with sn & rn and return
    players = []
    for entry in sn_rn_map:
        pid = entry["player_id"]
        pdata = id_to_data.get(pid)
        if not pdata:
            continue
        players.append({
            "player_id": pid,
            "name": pdata["name"],
            "sn": entry["sn"],
            "rn": entry["rn"],
            "current_ability": pdata["current_ability"],
            "height": pdata["height"],
            "weight": pdata["weight"],
            "attributes": normalise_attrs(pdata["attributes"])
        })

    return team_name, players
