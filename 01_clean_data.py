"""
Step 1: Data Cleaning & Preprocessing
Bird Species Observation Analysis - Forest & Grassland Ecosystems

Reads all sheets from both source workbooks, consolidates into a single
analysis-ready dataset, handles missing values/duplicates/dtype issues,
and writes the cleaned dataset to CSV + SQLite.
"""

import pandas as pd
import numpy as np
import sqlite3
import os

RAW_DIR = "/mnt/user-data/uploads"
OUT_DIR = "/home/claude/project/data"
os.makedirs(OUT_DIR, exist_ok=True)

ADMIN_UNIT_NAMES = {
    "ANTI": "Antietam National Battlefield",
    "CATO": "Catoctin Mountain Park",
    "CHOH": "Chesapeake & Ohio Canal NHP",
    "GWMP": "George Washington Memorial Parkway",
    "HAFE": "Harpers Ferry NHP",
    "MANA": "Manassas National Battlefield Park",
    "MONO": "Monocacy National Battlefield",
    "NACE": "National Capital East Parks",
    "PRWI": "Prince William Forest Park",
    "ROCR": "Rock Creek Park",
    "WOTR": "Wolf Trap National Park for the Performing Arts",
}


def load_workbook(filename, location_type):
    """Load all non-empty sheets from a workbook into one DataFrame."""
    path = os.path.join(RAW_DIR, filename)
    sheets = pd.read_excel(path, sheet_name=None)
    frames = []
    for sheet_name, df in sheets.items():
        if len(df) == 0:
            continue
        df = df.copy()
        df["Admin_Unit_Sheet"] = sheet_name  # ground-truth sheet/unit code
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined["Location_Type"] = location_type  # standardize/enforce
    return combined


def standardize_schema(df):
    """Align Forest/Grassland schema differences into one common shape."""
    df = df.copy()

    # Unify the taxon-code column name (Forest: NPSTaxonCode, Grassland: TaxonCode)
    if "NPSTaxonCode" in df.columns and "TaxonCode" in df.columns:
        df["Taxon_Code"] = df["NPSTaxonCode"].combine_first(df["TaxonCode"])
        df.drop(columns=["NPSTaxonCode", "TaxonCode"], inplace=True)
    elif "NPSTaxonCode" in df.columns:
        df.rename(columns={"NPSTaxonCode": "Taxon_Code"}, inplace=True)
    elif "TaxonCode" in df.columns:
        df.rename(columns={"TaxonCode": "Taxon_Code"}, inplace=True)

    # Site_Name only exists for Forest; add as NA for Grassland for a consistent shape
    if "Site_Name" not in df.columns:
        df["Site_Name"] = pd.NA

    # Previously_Obs only exists for Grassland; add as NA for Forest
    if "Previously_Obs" not in df.columns:
        df["Previously_Obs"] = pd.NA

    return df


def clean(df):
    df = df.copy()
    report = {}

    # --- Duplicates ---
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)

    # --- Admin unit name lookup ---
    df["Admin_Unit_Name"] = df["Admin_Unit_Code"].map(ADMIN_UNIT_NAMES)

    # --- Dates / temporal fields ---
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.month_name()

    def season_from_month(m):
        if pd.isna(m):
            return np.nan
        m = int(m)
        if m in (12, 1, 2):
            return "Winter"
        if m in (3, 4, 5):
            return "Spring"
        if m in (6, 7, 8):
            return "Summer"
        return "Fall"

    df["Season"] = df["Month"].apply(season_from_month)

    # Start/End time -> proper time objects + observation duration in minutes
    def parse_time(t):
        if pd.isna(t):
            return pd.NaT
        if isinstance(t, str):
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return pd.to_datetime(t, format=fmt).time()
                except ValueError:
                    continue
            return pd.NaT
        try:
            return t.time()
        except AttributeError:
            return t

    df["Start_Time"] = df["Start_Time"].apply(parse_time)
    df["End_Time"] = df["End_Time"].apply(parse_time)

    def duration_minutes(row):
        s, e = row["Start_Time"], row["End_Time"]
        if pd.isna(s) or pd.isna(e):
            return np.nan
        s_min = s.hour * 60 + s.minute
        e_min = e.hour * 60 + e.minute
        d = e_min - s_min
        return d if d >= 0 else np.nan  # negative => bad data, treat as missing

    df["Observation_Duration_Min"] = df.apply(duration_minutes, axis=1)

    # --- Categorical text cleanup (trim whitespace, consistent case where useful) ---
    text_cols = [
        "Observer", "ID_Method", "Distance", "Sex", "Common_Name",
        "Scientific_Name", "AOU_Code", "Sky", "Wind", "Disturbance",
        "Interval_Length", "Sub_Unit_Code", "Site_Name",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    # --- Missing value handling ---
    # Sex: many NaNs genuinely mean "not recorded / not visually sexed" -> explicit category
    df["Sex"] = df["Sex"].fillna("Not Recorded")

    # Distance: small number of missing -> explicit category rather than dropping rows
    df["Distance"] = df["Distance"].fillna("Not Recorded")

    # Sub_Unit_Code: almost entirely missing (esp. all of Grassland) -> keep as NA, not a data error
    # AcceptedTSN / Taxon_Code: small number missing -> leave NaN (used for joins/lookups only)

    # Boolean columns: ensure proper bool dtype, default missing Previously_Obs (Forest) to NA (kept as-is; not applicable)
    bool_cols = ["Flyover_Observed", "PIF_Watchlist_Status", "Regional_Stewardship_Status", "Initial_Three_Min_Cnt"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype("boolean")

    # --- Outlier checks on numeric environmental fields ---
    # Temperature (F) and Humidity (%) - flag implausible values rather than silently dropping
    report["temp_out_of_range"] = int(((df["Temperature"] < -20) | (df["Temperature"] > 120)).sum())
    report["humidity_out_of_range"] = int(((df["Humidity"] < 0) | (df["Humidity"] > 100)).sum())

    return df, report


def main():
    print("Loading Forest workbook...")
    forest = load_workbook("Bird_Monitoring_Data_FOREST.XLSX", "Forest")
    print(f"  Forest raw rows: {len(forest)}")

    print("Loading Grassland workbook...")
    grass = load_workbook("Bird_Monitoring_Data_GRASSLAND.XLSX", "Grassland")
    print(f"  Grassland raw rows: {len(grass)}")

    forest = standardize_schema(forest)
    grass = standardize_schema(grass)

    combined = pd.concat([forest, grass], ignore_index=True)
    print(f"\nCombined raw rows: {len(combined)}")

    cleaned, report = clean(combined)
    print(f"Cleaned rows (after dedup): {len(cleaned)}")
    print("Cleaning report:", report)

    # Save outputs
    csv_path = os.path.join(OUT_DIR, "bird_observations_clean.csv")
    cleaned.to_csv(csv_path, index=False)
    print(f"\nSaved cleaned CSV -> {csv_path}")

    db_path = os.path.join(OUT_DIR, "bird_observations.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cleaned.to_sql("bird_observations", conn, index=False, if_exists="replace")
    conn.close()
    print(f"Saved SQLite DB -> {db_path}")

    # Write a short cleaning summary for documentation
    summary_path = os.path.join(OUT_DIR, "cleaning_report.txt")
    with open(summary_path, "w") as f:
        f.write("DATA CLEANING SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Forest raw rows: {len(forest)}\n")
        f.write(f"Grassland raw rows: {len(grass)}\n")
        f.write(f"Combined raw rows: {len(forest) + len(grass)}\n")
        f.write(f"Duplicate rows removed: {report['duplicates_removed']}\n")
        f.write(f"Final cleaned rows: {len(cleaned)}\n\n")
        f.write("Schema reconciliation:\n")
        f.write("- NPSTaxonCode (Forest) and TaxonCode (Grassland) merged into Taxon_Code\n")
        f.write("- Site_Name (Forest-only) and Previously_Obs (Grassland-only) preserved as NA where absent\n\n")
        f.write("Missing value handling:\n")
        f.write("- Sex: missing -> 'Not Recorded' (explicit category, not dropped)\n")
        f.write("- Distance: missing -> 'Not Recorded'\n")
        f.write("- Sub_Unit_Code: left as NA (field is structurally absent for most/all Grassland records)\n")
        f.write("- AcceptedTSN / Taxon_Code: left as NA where missing (used only for lookups)\n\n")
        f.write(f"Temperature values out of plausible range (-20 to 120F): {report['temp_out_of_range']}\n")
        f.write(f"Humidity values out of plausible range (0-100%): {report['humidity_out_of_range']}\n")
        f.write("\nDerived columns added: Month, Month_Name, Season, Observation_Duration_Min, Admin_Unit_Name\n")
    print(f"Saved cleaning report -> {summary_path}")


if __name__ == "__main__":
    main()
