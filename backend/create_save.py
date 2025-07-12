import json
import os
import shutil
import sqlite3  # ✅ Required for DB connection
from save_helpers import create_save, assign_manager_to_save, update_metadata

# ✅ Load JSON payload first
with open("tmp/new_save.json") as f:
    data = json.load(f)

save_name = data["save_name"]
manager_name = data["manager_name"]
club_id = data.get("club_id")
nation_id = data.get("nation_id")

# ✅ Ensure saves dir exists
save_dir = os.path.join("saves")
os.makedirs(save_dir, exist_ok=True)

# ✅ Copy base DB to new save
base_db = os.path.join("database", "GameData.db")
save_path = os.path.join(save_dir, f"{save_name}.db")
shutil.copy(base_path, save_path)
print("✅ New save created at:", save_path)

# ✅ Now call logic helpers
assign_manager_to_save(save_path, manager_name, club_id, nation_id)
update_metadata(save_name, manager_name, club_id, nation_id)
