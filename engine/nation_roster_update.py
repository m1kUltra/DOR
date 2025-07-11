import sqlite3

def update_national_team_rosters(db_path):
    # Connect to SQLite DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing rosters and reset AUTOINCREMENT counter
        cursor.execute("DELETE FROM national_team_rosters;")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='national_team_rosters';")
        
        # Insert updated player -> nation_team mappings
        cursor.execute("""
            INSERT INTO national_team_rosters (nation_team_id, player_id)
            SELECT nt.nation_team_id, p.player_id
            FROM players p
            JOIN national_teams nt ON p.nation_id = nt.nation_id
        """)
        
        conn.commit()
        print("National team rosters updated successfully.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        conn.rollback()
        
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = 'GameData.db'
    update_national_team_rosters(db_path)
