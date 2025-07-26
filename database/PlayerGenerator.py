import pandas as pd
import sqlite3
import json
import random

DB_PATH = "GameData.db"
INPUT_XLSX = "templates_for_dor.xlsx"
OUTPUT_XLSX = "players_filled.xlsx"

TECHNICAL_ATTRS = ["darts","finishing","footwork","goal_kicking","handling","kicking",
                   "kicking_power","lineouts","marking","offloading","passing",
                   "scrummaging","rucking","technique"]

MENTAL_ATTRS = ["aggression","anticipation","bravery","composure","concentration",
                "decisions","determination","flair","leadership","off_the_ball",
                "positioning","teamwork","vision","work_rate"]

PHYSICAL_ATTRS = ["acceleration","agility","balance","jumping_reach",
                  "natural_fitness","pace","stamina","strength"]

VISIBLE_ATTRS = TECHNICAL_ATTRS + MENTAL_ATTRS + PHYSICAL_ATTRS

# ------------------- LOAD DB DATA -------------------
with sqlite3.connect(DB_PATH) as conn:
    archetypes_df = pd.read_sql("SELECT * FROM archetypes", conn)
    personalities_df = pd.read_sql("SELECT * FROM personalities", conn)
    ca_df = pd.read_sql("SELECT * FROM CA", conn)

# ---- Build archetype lookup: ranges ----
archetype_lookup = {}
for _, row in archetypes_df.iterrows():
    try:
        raw = json.loads(row["attr_weights_json"])
        parsed = {}
        for attr, val in raw.items():
            parts = [p.strip() for p in val.replace("–", "-").split(",")]
            if len(parts) == 2:
                lo, hi = float(parts[0]), float(parts[1])
            else:
                lo = hi = float(parts[0])
            parsed[attr] = (lo, hi)
        archetype_lookup[row["archetype_id"]] = parsed
    except Exception as e:
        print(f"⚠️ Error parsing archetype {row['archetype_id']}: {e}")

# ---- Build personality lookup: ranges ----
personality_lookup = {}
for _, row in personalities_df.iterrows():
    try:
        hidden = json.loads(row["hidden_weights_json"])
        parsed = {}
        for attr, val in hidden.items():
            parts = [p.strip() for p in val.replace("–", "-").split(",")]
            if len(parts) == 2:
                lo, hi = float(parts[0]), float(parts[1])
            else:
                lo = hi = float(parts[0])
            parsed[attr] = (lo, hi)
        personality_lookup[row["personality_id"]] = parsed
    except Exception as e:
        print(f"⚠️ Error parsing personality {row['personality_id']}: {e}")

# ---- Build CA cost lookup ----
ca_cost_lookup = {}
try:
    cost_json = json.loads(ca_df.iloc[0]["weights"])
    for attr, cost in cost_json.items():
        ca_cost_lookup[attr] = float(cost)
    
except Exception as e:
    print(f"⚠️ Error parsing CA cost weights: {e}")

# ------------------- LOAD PLAYERS -------------------
players_df = pd.read_excel(INPUT_XLSX, sheet_name="players")

# ------------------- FILL LOGIC -------------------
filled_rows = []

for _, row in players_df.iterrows():
    new_row = {}

    # copy over basic fields from input
    for col in [
        "player_id","firstname","surname","dob","height","weight","nationalities",
        "current_ability","club","franchise","relationships","condition",
        "contract","position","archetype","reputation","traits","injuries",
        "current_injury_return","bans","current_ban","growthscore","growth_details",
        "personality","status","season_stats","history"
    ]:
        new_row[col] = row[col] if col in row else None

    ca_val = float(row.get("current_ability", 0))
    arch_id = row.get("archetype")
    pers_id = row.get("personality")
    skill_points_target = ca_val * 6.0

    # -- Step 1: randomize visible attributes within archetype min/max
    arch_ranges = archetype_lookup.get(arch_id, {})
    values = {}
    for attr in VISIBLE_ATTRS:
        lo, hi = arch_ranges.get(attr, (1.0, 20.0))
        values[attr] = random.uniform(lo, hi)

    # -- Helper: compute skill points used
    def compute_points(vals):
        total = 0.0
        for a in VISIBLE_ATTRS:
            cost = ca_cost_lookup.get(a, 1.0)
            total += vals[a] * cost  # match Excel formula
        return total

    used = compute_points(values)


    # -- Step 2: add if below target
    if used < skill_points_target:
        while skill_points_target - used > 1:
            progress = False
            attrs_shuffled = VISIBLE_ATTRS.copy()
            random.shuffle(attrs_shuffled)
            for a in attrs_shuffled:
                lo, hi = arch_ranges.get(a, (1.0, 20.0))
                cost = ca_cost_lookup.get(a, 1.0)
                if values[a] + 1 <= hi and (used + cost) <= skill_points_target:
                    values[a] += 1
                    used += cost
                    progress = True
            if not progress:
                break

    # -- Step 3: reduce if above target
    elif used > skill_points_target:
        while used - skill_points_target > 1:
            progress = False
            attrs_shuffled = VISIBLE_ATTRS.copy()
            random.shuffle(attrs_shuffled)
            for a in attrs_shuffled:
                lo, hi = arch_ranges.get(a, (1.0, 20.0))
                cost = ca_cost_lookup.get(a, 1.0)
                if values[a] - 1 >= lo:
                    values[a] -= 1
                    used -= cost
                    progress = True
                    if used <= skill_points_target:
                        break
            if not progress:
                break

    # -- Store all visible attributes as JSON
    attr_dict = {a: round(values[a], 0) for a in VISIBLE_ATTRS}
    new_row["attributes"] = json.dumps(attr_dict)

    # -- Hidden attributes
    hidden_vals = {}
    pers_ranges = personality_lookup.get(pers_id, {})
    for attr, (lo, hi) in pers_ranges.items():
        hidden_vals[attr] = round(random.uniform(lo, hi), 1)
    new_row["hidden_attributes"] = json.dumps(hidden_vals)

    filled_rows.append(new_row)

filled_df = pd.DataFrame(filled_rows)

# ------------------- SAVE OUTPUT -------------------
filled_df.to_excel(OUTPUT_XLSX, index=False)
print(f"✅ Players filled and saved to {OUTPUT_XLSX}")

with sqlite3.connect(DB_PATH) as conn:
    filled_df.to_sql("players", conn, if_exists="replace", index=False)
    print("✅ Players table in DB updated.")
