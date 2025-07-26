import pandas as pd
import sqlite3
import json

DB_PATH = "GameData.db"
INPUT_XLSX = "templates_for_dor.xlsx"

# --- Attribute groups ---
TECHNICAL_ATTRS = ["darts","finishing","footwork","goal_kicking","handling","kicking","kicking_power",
                   "lineouts","marking","offloading","passing","scrummaging","rucking","technique"]
MENTAL_ATTRS = ["aggression","anticipation","bravery","composure","concentration","decisions",
                "determination","flair","leadership","off_the_ball","positioning","teamwork","vision","work_rate"]
PHYSICAL_ATTRS = ["acceleration","agility","balance","jumping_reach","natural_fitness","pace","stamina","strength"]

# --- Read sheets ---
archetypes_df = pd.read_excel(INPUT_XLSX, sheet_name="archetypes")
personalities_df = pd.read_excel(INPUT_XLSX, sheet_name="personalities")

# --- Build archetypes rows ---
archetype_rows = []
for _, row in archetypes_df.iterrows():
    attr_dict = {}
    for attr in TECHNICAL_ATTRS + MENTAL_ATTRS + PHYSICAL_ATTRS:
        val = str(row.get(attr, "")).strip()
        if pd.notna(val) and val != "" and val.lower() != "nan":
            attr_dict[attr] = val
    archetype_rows.append({
        "archetype_id": int(row.get("archetype_id")) if pd.notna(row.get("archetype_id")) else None,
        "name": row.get("name"),
        "pos_code": row.get("pos_code"),
        "attr_weights_json": json.dumps(attr_dict)
    })

# --- Build personalities rows ---
personality_rows = []
for _, row in personalities_df.iterrows():
    hidden_dict = {}
    for attr in personalities_df.columns[2:]:  # skip id and name
        val = str(row.get(attr, "")).strip()
        if pd.notna(val) and val != "" and val.lower() != "nan":
            hidden_dict[attr] = val
    personality_rows.append({
        "personality_id": int(row.get("personality_id")) if pd.notna(row.get("personality_id")) else None,
        "name": row.get("name"),
        "hidden_weights_json": json.dumps(hidden_dict)
    })

# --- Convert to DataFrames ---
archetypes_out = pd.DataFrame(archetype_rows)
personalities_out = pd.DataFrame(personality_rows)

# --- Insert into DB ---
with sqlite3.connect(DB_PATH) as conn:
    archetypes_out.to_sql("archetypes", conn, if_exists="replace", index=False)
    print("✅ Inserted archetypes into DB (with attr_weights_json).")
    personalities_out.to_sql("personalities", conn, if_exists="replace", index=False)
    print("✅ Inserted personalities into DB (with hidden_weights_json).")

print("✅ Done!")
