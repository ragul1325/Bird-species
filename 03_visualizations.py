"""
Step 3: Data Visualization (static charts for the report).
Bird Species Observation Analysis - Forest & Grassland Ecosystems
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

DB_PATH = "/home/claude/project/data/bird_observations.db"
OUT_DIR = "/home/claude/project/outputs/charts"
os.makedirs(OUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.0)
PALETTE = {"Forest": "#2d6a4f", "Grassland": "#bc6c25"}

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM bird_observations", conn)
conn.close()

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved", path)


# 1. Species diversity & total observations by habitat
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
totals = df.groupby("Location_Type").size()
species = df.groupby("Location_Type")["Scientific_Name"].nunique()
axes[0].bar(totals.index, totals.values, color=[PALETTE[i] for i in totals.index])
axes[0].set_title("Total Observations by Habitat")
axes[0].set_ylabel("Observations")
axes[1].bar(species.index, species.values, color=[PALETTE[i] for i in species.index])
axes[1].set_title("Unique Species by Habitat")
axes[1].set_ylabel("Species Count")
fig.tight_layout()
save(fig, "01_habitat_overview.png")


# 2. Top 10 species per habitat (side by side)
fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=False)
for ax, loc in zip(axes, ["Forest", "Grassland"]):
    top = (df[df.Location_Type == loc]["Common_Name"]
           .value_counts().head(10).sort_values())
    ax.barh(top.index, top.values, color=PALETTE[loc])
    ax.set_title(f"Top 10 Species – {loc}")
    ax.set_xlabel("Observations")
fig.tight_layout()
save(fig, "02_top_species.png")


# 3. Seasonal trends
fig, ax = plt.subplots(figsize=(8, 4.5))
season_order = ["Spring", "Summer", "Fall", "Winter"]
pivot = (df.groupby(["Season", "Location_Type"]).size()
         .unstack(fill_value=0).reindex(season_order).dropna(how="all"))
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c) for c in pivot.columns])
ax.set_title("Observations by Season and Habitat")
ax.set_ylabel("Observations")
ax.set_xlabel("Season")
fig.tight_layout()
save(fig, "03_seasonal_trends.png")


# 4. Admin unit hotspots
fig, ax = plt.subplots(figsize=(9, 5))
unit_counts = (df.groupby(["Admin_Unit_Code", "Location_Type"]).size()
               .reset_index(name="count")
               .sort_values("count", ascending=True))
colors = unit_counts["Location_Type"].map(PALETTE)
ax.barh(unit_counts["Admin_Unit_Code"] + " (" + unit_counts["Location_Type"].str[0] + ")",
        unit_counts["count"], color=colors)
ax.set_title("Observations by Administrative Unit")
ax.set_xlabel("Observations")
fig.tight_layout()
save(fig, "04_admin_unit_hotspots.png")


# 5. ID Method distribution
fig, ax = plt.subplots(figsize=(7, 4.5))
pivot = df.groupby(["ID_Method", "Location_Type"]).size().unstack(fill_value=0)
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c) for c in pivot.columns])
ax.set_title("Identification Method by Habitat")
ax.set_ylabel("Observations")
plt.xticks(rotation=20)
fig.tight_layout()
save(fig, "05_id_method.png")


# 6. Temperature vs observation count (binned)
fig, ax = plt.subplots(figsize=(8, 4.5))
df["Temp_Bin"] = pd.cut(df["Temperature"], bins=range(10, 40, 3))
pivot = df.groupby(["Temp_Bin", "Location_Type"], observed=True).size().unstack(fill_value=0)
pivot.plot(kind="line", marker="o", ax=ax, color=[PALETTE.get(c) for c in pivot.columns])
ax.set_title("Observation Count by Temperature Range")
ax.set_xlabel("Temperature (°F, binned)")
ax.set_ylabel("Observations")
plt.xticks(rotation=45)
fig.tight_layout()
save(fig, "06_temperature_effect.png")


# 7. Disturbance effect
fig, ax = plt.subplots(figsize=(8, 4.5))
order = ["No effect on count", "Slight effect on count", "Moderate effect on count", "Serious effect on count"]
pivot = df.groupby(["Disturbance", "Location_Type"]).size().unstack(fill_value=0).reindex(order)
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c) for c in pivot.columns])
ax.set_title("Disturbance Level vs Observations")
ax.set_ylabel("Observations")
plt.xticks(rotation=20, ha="right")
fig.tight_layout()
save(fig, "07_disturbance_effect.png")


# 8. Conservation watchlist species
fig, ax = plt.subplots(figsize=(8, 5))
watch = (df[df.PIF_Watchlist_Status == 1]
         .groupby(["Common_Name", "Location_Type"]).size()
         .reset_index(name="count").sort_values("count"))
colors = watch["Location_Type"].map(PALETTE)
ax.barh(watch["Common_Name"] + " (" + watch["Location_Type"].str[0] + ")", watch["count"], color=colors)
ax.set_title("PIF Watchlist (At-Risk) Species Observations")
ax.set_xlabel("Observations")
fig.tight_layout()
save(fig, "08_watchlist_species.png")


# 9. Distance distribution
fig, ax = plt.subplots(figsize=(7, 4.5))
order = ["<= 50 Meters", "50 - 100 Meters", "Not Recorded"]
pivot = df.groupby(["Distance", "Location_Type"]).size().unstack(fill_value=0).reindex(order)
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c) for c in pivot.columns])
ax.set_title("Observation Distance from Observer")
ax.set_ylabel("Observations")
plt.xticks(rotation=15)
fig.tight_layout()
save(fig, "09_distance_distribution.png")


# 10. Observer activity
fig, ax = plt.subplots(figsize=(8, 4.5))
pivot = df.groupby(["Observer", "Location_Type"]).size().unstack(fill_value=0)
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c) for c in pivot.columns])
ax.set_title("Observations Logged per Observer")
ax.set_ylabel("Observations")
plt.xticks(rotation=15)
fig.tight_layout()
save(fig, "10_observer_activity.png")

print("\nAll charts generated.")
