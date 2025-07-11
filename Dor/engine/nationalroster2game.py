import sqlite3
import json
import os

def export_team_rosters(db_path, output_folder):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Make sure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get all teams
    cursor.execute("SELECT nation_team_id, team_name FROM national_teams")
    teams = cursor.fetchall()  # List of (nation_team_id, team_name)

    for nation_team_id, team_name in teams:
        # Get all players for this team with full player info
        cursor.execute("""
            SELECT p.player_id, p.name, p.nation_id, p.current_ability
            FROM national_team_rosters ntr
            JOIN players p ON ntr.player_id = p.player_id
            WHERE ntr.nation_team_id = ?
        """, (nation_team_id,))
        players = cursor.fetchall()

        # Convert players to list of dicts
        players_list = []
        for player in players:
            player_dict = {
                'player_id': player[0],
                'name': player[1],
                'nation_id': player[2],
                'current_ability': player[3]
            }
            players_list.append(player_dict)

        # Create filename safe team name
        safe_team_name = "".join(c for c in team_name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = os.path.join(output_folder, f"{safe_team_name}_roster.json")

        # Save JSON
        with open(filename, 'w') as f:
            json.dump(players_list, f, indent=4)

        print(f"Saved roster for team '{team_name}' ({nation_team_id}) with {len(players_list)} players to {filename}")

    conn.close()


if __name__ == "__main__":
    db_path = '/Users/dairekelly/Documents/gamedata/GameData.db'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, 'national_rosters')
    os.makedirs(output_folder, exist_ok=True)
    export_team_rosters(db_path, output_folder)
