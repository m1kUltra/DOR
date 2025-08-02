import sqlite3
import json

def load_team_from_db(db_path, nation_team_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get team name and squad JSON
    cursor.execute("SELECT team_name, squad_json FROM national_teams WHERE nation_team_id = ?", (nation_team_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"No team found with ID {nation_team_id}")

    team_name, squad_json = row
    squad_data = json.loads(squad_json or "{}")
    selection = squad_data.get("selection", {})
    starters = selection.get("starters", [])

    player_ids = [p["player_id"] for p in starters if "player_id" in p]
    if not player_ids:
        raise ValueError(f"No valid starters found for team {team_name}")

    # Get player info from database
    placeholders = ",".join(["?"] * len(player_ids))
    cursor.execute(f"""
        SELECT player_id, firstname, surname, current_ability
        FROM players
        WHERE player_id IN ({placeholders})
    """, player_ids)

    players = [
        {
            "player_id": pid,
            "name": f"{first} {last}",
            "current_ability": ca
        }
        for pid, first, last, ca in cursor.fetchall()
    ]

    conn.close()
    return team_name, players
