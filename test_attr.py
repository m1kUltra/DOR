import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
TRIALS = 100
EXPONENTS = range(1, 13)
ATTR_VALUE = 20
defender = 5

norm_val = ((ATTR_VALUE - 1) / 19) ** 0.8
def_val =((defender - 1) / 19) ** 0.8

summary_rows = []
all_results = {}

for exp in EXPONENTS:
    norm_val_pow = norm_val ** exp
    def_val_pow = def_val ** exp
    scores = [
        norm_val_pow * random.random() - def_val_pow * random.random()
        for _ in range(TRIALS)
    ]
    arr = np.array(scores)
    
    # Scale factor for normalization to [-1, 1]
    scale_factor = max(abs(arr.min()), abs(arr.max()))
    normed = arr / scale_factor if scale_factor != 0 else arr
    
    summary_rows.append({
        "Exponent": exp,
        "Mean_raw": arr.mean(),
        "StdDev_raw": arr.std(ddof=1),
        "Min_raw": arr.min(),
        "Max_raw": arr.max(),
        "ScaleFactor": scale_factor,
        "Mean_norm": normed.mean(),
        "StdDev_norm": normed.std(ddof=1),
        "Min_norm": normed.min(),
        "Max_norm": normed.max()
    })
    
    all_results[exp] = normed

# Create summary DataFrame
df = pd.DataFrame(summary_rows)
df.to_csv("norm_val_pow_results_with_norm.csv", index=False)
print(df)

# Scatterplot grid for normed results
cols = 4
rows = int(np.ceil(len(EXPONENTS) / cols))
fig, axes = plt.subplots(rows, cols, figsize=(cols * 3, rows * 2), sharey=True)

for idx, exp in enumerate(EXPONENTS):
    ax = axes[idx // cols, idx % cols]
    ax.scatter(range(TRIALS), all_results[exp], s=5, alpha=0.5)
    ax.set_title(f"Exp {exp}")
    ax.set_ylim(-1.05, 1.05)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
    ax.tick_params(axis='x', labelsize=6)
    ax.tick_params(axis='y', labelsize=6)

# Hide any unused subplots
for idx in range(len(EXPONENTS), rows * cols):
    fig.delaxes(axes[idx // cols, idx % cols])

fig.suptitle("Normed score scatterplots per exponent", fontsize=14)
plt.tight_layout()
plt.savefig("normed_scatterplots.png", dpi=150)
plt.show()
