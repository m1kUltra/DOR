import os
import json
import shutil
import sqlite3
from datetime import datetime

SAVE_DIR = "saves"
METADATA_PATH = os.path.join(SAVE_DIR, "metadata.json")
BASE_DB = "database/base.db"

def load_metadata():
    if not os.path.exists(METADATA_PATH):
        return {}
    with open(METADATA_PATH, "r") as f:
        return json.load(f)

def save_metadata(data):
    with open(METADATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def create_save(save_name, manager_name, club_id=None, nation_id=None):
    metadata = load_metadata()
    save_id = f"save_{len(metadata)+1:02}"
    save_path = os.path.join(SAVE_DIR, f"{save_id}.db")

    shutil.copyfile(BASE_DB, save_path)

    # Connect to new save DB
    conn = sqlite3.connect(save_path)
    cursor = conn.cursor()

    # Insert manager
    cursor.execute("INSERT INTO managers (name, is_user) VALUES (?, 1)", (manager_name,))
    manager_id = cursor.lastrowid

    if club_id:
        cursor.execute("UPDATE clubs SET manager_id = ? WHERE club_id = ?", (manager_id, club_id))
    if nation_id:
        cursor.execute("UPDATE nations SET manager_id = ? WHERE nation_id = ?", (manager_id, nation_id))

    conn.commit()
    conn.close()

    metadata[save_id] = {
        "name": save_name,
        "manager": manager_name,
        "club_id": club_id,
        "nation_id": nation_id,
        "manager_id": manager_id,
        "last_played": datetime.now().isoformat()
    }
    save_metadata(metadata)

    return save_id
