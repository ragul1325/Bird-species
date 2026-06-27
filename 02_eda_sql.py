"""
Step 2: Exploratory Data Analysis via SQL queries against SQLite.
Bird Species Observation Analysis - Forest & Grassland Ecosystems
"""

import sqlite3
import pandas as pd
import os

DB_PATH = "/home/claude/project/data/bird_observations.db"
OUT_DIR = "/home/claude/project/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

def q(sql):
    return pd.read_sql_query(sql, conn)

results = {}

print("=" * 70)
print("1. OVERALL COUNTS & SPECIES DIVERSITY BY HABITAT")
print("=" * 70)
r = q("""
    SELECT Location_Type,
           COUNT(*) AS total_observations,
           COUNT(DISTINCT Scientific_Name) AS unique_species,
           COUNT(DISTINCT Admin_Unit_Code) AS admin_units,
           COUNT(DISTINCT Observer) AS observers
    FROM bird_observations
    GROUP BY Location_Type
""")
print(r.to_string(index=False))
results["diversity_by_habitat"] = r

print("\n" + "=" * 70)
print("2. TOP 10 MOST OBSERVED SPECIES PER HABITAT")
print("=" * 70)
r = q("""
    SELECT Location_Type, Common_Name, COUNT(*) AS observations
    FROM bird_observations
    GROUP BY Location_Type, Common_Name
    ORDER BY Location_Type, observations DESC
""")
top10 = r.groupby("Location_Type").head(10)
print(top10.to_string(index=False))
results["top_species_by_habitat"] = top10

print("\n" + "=" * 70)
print("3. OBSERVATIONS BY ADMIN UNIT (SPATIAL HOTSPOTS)")
print("=" * 70)
r = q("""
    SELECT Admin_Unit_Code, Admin_Unit_Name, Location_Type,
           COUNT(*) AS observations,
           COUNT(DISTINCT Scientific_Name) AS species_count
    FROM bird_observations
    GROUP BY Admin_Unit_Code, Location_Type
    ORDER BY observations DESC
""")
print(r.to_string(index=False))
results["admin_unit_hotspots"] = r

print("\n" + "=" * 70)
print("4. SEASONAL / TEMPORAL TRENDS")
print("=" * 70)
r = q("""
    SELECT Location_Type, Year, Season, COUNT(*) AS observations
    FROM bird_observations
    GROUP BY Location_Type, Year, Season
    ORDER BY Year, Season
""")
print(r.to_string(index=False))
results["seasonal_trends"] = r

r2 = q("""
    SELECT Location_Type, Month_Name, Month, COUNT(*) AS observations
    FROM bird_observations
    GROUP BY Location_Type, Month_Name, Month
    ORDER BY Month
""")
results["monthly_trends"] = r2

print("\n" + "=" * 70)
print("5. ID METHOD / ACTIVITY PATTERNS")
print("=" * 70)
r = q("""
    SELECT Location_Type, ID_Method, COUNT(*) AS observations
    FROM bird_observations
    WHERE ID_Method IS NOT NULL
    GROUP BY Location_Type, ID_Method
    ORDER BY Location_Type, observations DESC
""")
print(r.to_string(index=False))
results["id_method_patterns"] = r

print("\n" + "=" * 70)
print("6. SEX RATIO BY HABITAT")
print("=" * 70)
r = q("""
    SELECT Location_Type, Sex, COUNT(*) AS observations
    FROM bird_observations
    GROUP BY Location_Type, Sex
    ORDER BY Location_Type, observations DESC
""")
print(r.to_string(index=False))
results["sex_ratio"] = r

print("\n" + "=" * 70)
print("7. ENVIRONMENTAL CONDITIONS vs OBSERVATIONS")
print("=" * 70)
r = q("""
    SELECT Location_Type,
           ROUND(AVG(Temperature),1) AS avg_temp,
           ROUND(AVG(Humidity),1) AS avg_humidity,
           ROUND(MIN(Temperature),1) AS min_temp,
           ROUND(MAX(Temperature),1) AS max_temp
    FROM bird_observations
    GROUP BY Location_Type
""")
print(r.to_string(index=False))
results["env_conditions_summary"] = r

print("\n" + "=" * 70)
print("8. DISTURBANCE EFFECT ON OBSERVATIONS")
print("=" * 70)
r = q("""
    SELECT Location_Type, Disturbance, COUNT(*) AS observations
    FROM bird_observations
    WHERE Disturbance IS NOT NULL
    GROUP BY Location_Type, Disturbance
    ORDER BY Location_Type, observations DESC
""")
print(r.to_string(index=False))
results["disturbance_effect"] = r

print("\n" + "=" * 70)
print("9. DISTANCE FROM OBSERVER")
print("=" * 70)
r = q("""
    SELECT Location_Type, Distance, COUNT(*) AS observations
    FROM bird_observations
    GROUP BY Location_Type, Distance
    ORDER BY Location_Type, observations DESC
""")
print(r.to_string(index=False))
results["distance_distribution"] = r

print("\n" + "=" * 70)
print("10. FLYOVER FREQUENCY")
print("=" * 70)
r = q("""
    SELECT Location_Type, Flyover_Observed, COUNT(*) AS observations
    FROM bird_observations
    GROUP BY Location_Type, Flyover_Observed
""")
print(r.to_string(index=False))
results["flyover_frequency"] = r

print("\n" + "=" * 70)
print("11. OBSERVER ACTIVITY")
print("=" * 70)
r = q("""
    SELECT Observer, Location_Type, COUNT(*) AS observations,
           COUNT(DISTINCT Scientific_Name) AS species_seen
    FROM bird_observations
    GROUP BY Observer, Location_Type
    ORDER BY observations DESC
    LIMIT 15
""")
print(r.to_string(index=False))
results["observer_activity"] = r

print("\n" + "=" * 70)
print("12. CONSERVATION WATCHLIST SPECIES")
print("=" * 70)
r = q("""
    SELECT Location_Type, Common_Name, Scientific_Name,
           COUNT(*) AS observations
    FROM bird_observations
    WHERE PIF_Watchlist_Status = 1
    GROUP BY Location_Type, Common_Name, Scientific_Name
    ORDER BY observations DESC
""")
print(r.to_string(index=False))
results["watchlist_species"] = r

r2 = q("""
    SELECT Location_Type,
           SUM(CASE WHEN PIF_Watchlist_Status = 1 THEN 1 ELSE 0 END) AS watchlist_obs,
           SUM(CASE WHEN Regional_Stewardship_Status = 1 THEN 1 ELSE 0 END) AS stewardship_obs,
           COUNT(*) AS total_obs
    FROM bird_observations
    GROUP BY Location_Type
""")
print(r2.to_string(index=False))
results["conservation_summary"] = r2

print("\n" + "=" * 70)
print("13. VISIT NUMBER vs SPECIES DIVERSITY")
print("=" * 70)
r = q("""
    SELECT Location_Type, Visit, COUNT(*) AS observations,
           COUNT(DISTINCT Scientific_Name) AS unique_species
    FROM bird_observations
    GROUP BY Location_Type, Visit
    ORDER BY Location_Type, Visit
""")
print(r.to_string(index=False))
results["visit_patterns"] = r

print("\n" + "=" * 70)
print("14. PLOT-LEVEL DIVERSITY (TOP 15 PLOTS)")
print("=" * 70)
r = q("""
    SELECT Plot_Name, Location_Type, COUNT(*) AS observations,
           COUNT(DISTINCT Scientific_Name) AS unique_species
    FROM bird_observations
    GROUP BY Plot_Name, Location_Type
    ORDER BY unique_species DESC
    LIMIT 15
""")
print(r.to_string(index=False))
results["plot_level_diversity"] = r

# Save all query results to a single Excel workbook for reference
xlsx_path = os.path.join(OUT_DIR, "eda_query_results.xlsx")
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    for name, df in results.items():
        df.to_excel(writer, sheet_name=name[:31], index=False)
print(f"\nAll query results saved -> {xlsx_path}")

conn.close()
