import json
import os
from save_helpers import create_save, assign_manager_to_save

# ✅ Load the save config
with open("tmp/new_save.json") as f:
    data = json.load(f)

save_name = data["save_name"]
manager_name = data["manager_name"]
club_id = data.get("club_id")
nation_id = data.get("nation_id")

# ✅ Create new save DB from GameData
save_path = create_save(save_name)

# ✅ Assign user manager to team
assign_manager_to_save(save_path, manager_name, club_id, nation_id)

print("✅ New save initialized and manager assigned.")
