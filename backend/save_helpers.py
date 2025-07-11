# backend/save_helpers.py
import shutil
import os
import sqlite3
import json
from datetime import datetime

def create_save(save_name):
    base_path = "database/base.db"
    save_dir = "saves"
    save_path = os.path.join(save_dir, f"{save_name}.db")
    os.makedirs(save_dir, exist_ok=True)
    shutil.copyfile(base_path, save_path)
    return save_path

def assign_manager_to_save(save_path, manager_name, club_id=None, nation_id=None):
    conn = sqlite3.connect(save_path)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO managers (name, is_user) VALUES (?, 1)", (manager_name,))
    manager_id = cursor.lastrowid

    if club_id:
        cursor.execute("UPDATE clubs SET manager_id = ? WHERE club_id = ?", (manager_id, club_id))
    if nation_id:
        cursor.execute("UPDATE nations SET manager_id = ? WHERE nation_id = ?", (manager_id, nation_id))

    conn.commit()
    conn.close()
    return manager_id

def update_metadata(save_name, manager_name, club_id=None, nation_id=None):
    metadata_path = "saves/metadata.json"
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        metadata = {}

    metadata[save_name] = {
        "manager": manager_name,
        "club_id": club_id,
        "nation_id": nation_id,
        "last_played": datetime.now().isoformat()
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
