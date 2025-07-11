import pandas as pd
import sqlite3
import os 
# File paths
excel_path = 'Gamedata.xlsx'
db_path = 'GameData.db'
print("Using DB at:", os.path.abspath(db_path))
print("Using DB at:", os.path.abspath(excel_path))
# Connect to SQLite DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Clear existing data from all tables you want to reload
tables_to_clear = ['players', 'nationalities', 'national_teams']
for table in tables_to_clear:
    cursor.execute(f"DELETE FROM {table};")
    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")  # reset AUTOINCREMENT counter

conn.commit()  # commit deletes before inserts

# 2. Load Excel sheets into dataframes
df_players = pd.read_excel(excel_path, sheet_name='players')
df_nation = pd.read_excel(excel_path, sheet_name='nationalities')
df_national_teams = pd.read_excel(excel_path, sheet_name='national_teams')


# 3. Insert rows into players table
for _, row in df_players.iterrows():
    cursor.execute("""
        INSERT INTO players (player_id, name, nation_id, current_ability)
        VALUES (?, ?, ?, ?)
    """, (row['player_id'], row['name'], row['nation_id'], row['current_ability']))

# 4. Insert rows into nation table
for _, row in df_nation.iterrows():
    cursor.execute("""
        INSERT INTO nationalities (nation_id, name)
        VALUES (?, ?)
    """, (row['nation_id'], row['name']))

# 5. Insert rows into national_teams table
for _, row in df_national_teams.iterrows():
    cursor.execute("""
        INSERT INTO national_teams (nation_team_id, nation_id, team_name)
        VALUES (?, ?, ?)
    """, (row['nation_team_id'], row['nation_id'], row['name']))
cursor.execute("SELECT COUNT(*) FROM players")
print("✅ Players in DB:", cursor.fetchone()[0])
cursor.execute("SELECT COUNT(*) FROM nationalities")
print("✅ Nationalities in DB:", cursor.fetchone()[0])
cursor.execute("SELECT COUNT(*) FROM national_teams")
print("✅ National Teams in DB:", cursor.fetchone()[0])
# Commit and close
conn.commit()
conn.close()
