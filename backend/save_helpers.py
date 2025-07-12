import shutil
import os
import sqlite3

def create_save(save_name):
    base_path = "database/GameData.db"
    save_dir = "saves"
    os.makedirs(save_dir, exist_ok=True)
    
    save_path = os.path.join(save_dir, f"{save_name}.db")
    shutil.copyfile(base_path, save_path)
    print(f"✅ Save created at: {save_path}")
    return save_path

def assign_manager_to_save(save_path, manager_name, club_id=None, nation_id=None):
    conn = sqlite3.connect(save_path)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO managers (name, is_user) VALUES (?, 1)", (manager_name,))
    manager_id = cursor.lastrowid

    if club_id:
        cursor.execute("UPDATE clubs SET manager_id = ? WHERE club_id = ?", (manager_id, club_id))
    if nation_id:
        cursor.execute("UPDATE national_teams SET manager_id = ? WHERE nation_team_id = ?", (manager_id, nation_id))

    conn.commit()
    conn.close()
    return manager_id
