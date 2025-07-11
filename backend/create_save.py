import json
from save_helpers import create_save, assign_manager_to_save, update_metadata

with open("tmp/new_save.json") as f:
    data = json.load(f)

save_name = data["save_name"]
manager_name = data["manager_name"]
club_id = data.get("club_id")
nation_id = data.get("nation_id")

# ✅ Step 1: Copy base.db → saves/save_name.db
save_path = create_save(save_name)

# ✅ Step 2: Write manager into that save
assign_manager_to_save(save_path, manager_name, club_id, nation_id)

# ✅ Step 3: Add JSON metadata for launcher UI
update_metadata(save_name, manager_name, club_id, nation_id)
