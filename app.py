"""
Interactive Streamlit Dashboard
Bird Species Observation Analysis - Forest & Grassland Ecosystems

Run with:
    pip install streamlit plotly pandas
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

st.set_page_config(page_title="Bird Species Observation Dashboard", layout="wide", page_icon="🐦")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bird_observations.db")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM bird_observations", conn)
    conn.close()
    df["Date"] = pd.to_datetime(df["Date"])
    return df


df = load_data()

st.title("🐦 Bird Species Observation Dashboard")
st.caption("Forest vs. Grassland ecosystems — National Capital Region parks")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

habitat_sel = st.sidebar.multiselect(
    "Habitat (Location Type)", options=sorted(df["Location_Type"].unique()),
    default=sorted(df["Location_Type"].unique())
)
unit_sel = st.sidebar.multiselect(
    "Administrative Unit", options=sorted(df["Admin_Unit_Code"].unique()),
    default=sorted(df["Admin_Unit_Code"].unique())
)
season_sel = st.sidebar.multiselect(
    "Season", options=sorted(df["Season"].dropna().unique()),
    default=sorted(df["Season"].dropna().unique())
)
species_options = sorted(df["Common_Name"].unique())
species_sel = st.sidebar.multiselect("Species (optional)", options=species_options, default=[])
watchlist_only = st.sidebar.checkbox("Show only PIF Watchlist species", value=False)

filtered = df[
    df["Location_Type"].isin(habitat_sel)
    & df["Admin_Unit_Code"].isin(unit_sel)
    & df["Season"].isin(season_sel)
]
if species_sel:
    filtered = filtered[filtered["Common_Name"].isin(species_sel)]
if watchlist_only:
    filtered = filtered[filtered["PIF_Watchlist_Status"] == 1]

st.sidebar.markdown(f"**{len(filtered):,}** observations match your filters")

# ---------------- KPI row ----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Observations", f"{len(filtered):,}")
col2.metric("Unique Species", filtered["Scientific_Name"].nunique())
col3.metric("Admin Units", filtered["Admin_Unit_Code"].nunique())
col4.metric("Watchlist Species", filtered.loc[filtered.PIF_Watchlist_Status == 1, "Common_Name"].nunique())

st.divider()

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Species", "Temporal", "Spatial", "Environment", "Conservation"]
)

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        top_species = filtered["Common_Name"].value_counts().head(15).sort_values()
        fig = px.bar(top_species, orientation="h", title="Top 15 Most Observed Species",
                     labels={"value": "Observations", "index": "Species"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        sex_counts = filtered.groupby(["Location_Type", "Sex"]).size().reset_index(name="count")
        fig = px.bar(sex_counts, x="Sex", y="count", color="Location_Type", barmode="group",
                     title="Sex Distribution by Habitat")
        st.plotly_chart(fig, use_container_width=True)

    id_method = filtered.groupby(["Location_Type", "ID_Method"]).size().reset_index(name="count")
    fig = px.bar(id_method, x="ID_Method", y="count", color="Location_Type", barmode="group",
                 title="Identification Method by Habitat")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        season_counts = filtered.groupby(["Season", "Location_Type"]).size().reset_index(name="count")
        fig = px.bar(season_counts, x="Season", y="count", color="Location_Type", barmode="group",
                     title="Observations by Season",
                     category_orders={"Season": ["Spring", "Summer", "Fall", "Winter"]})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        monthly = filtered.groupby(["Month", "Location_Type"]).size().reset_index(name="count")
        fig = px.line(monthly, x="Month", y="count", color="Location_Type", markers=True,
                       title="Observations by Month")
        st.plotly_chart(fig, use_container_width=True)

    daily = filtered.groupby(filtered["Date"].dt.date).size().reset_index(name="count")
    daily.columns = ["Date", "count"]
    fig = px.line(daily, x="Date", y="count", title="Daily Observation Volume")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    unit_counts = filtered.groupby(["Admin_Unit_Code", "Admin_Unit_Name", "Location_Type"]).size().reset_index(name="count")
    fig = px.bar(unit_counts, x="Admin_Unit_Code", y="count", color="Location_Type",
                 hover_data=["Admin_Unit_Name"], title="Observations by Administrative Unit")
    st.plotly_chart(fig, use_container_width=True)

    plot_div = (filtered.groupby(["Plot_Name", "Location_Type"])["Scientific_Name"]
                .nunique().reset_index(name="unique_species")
                .sort_values("unique_species", ascending=False).head(20))
    fig = px.bar(plot_div, x="Plot_Name", y="unique_species", color="Location_Type",
                 title="Top 20 Plots by Species Diversity")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(filtered, x="Temperature", color="Location_Type", barmode="overlay",
                            opacity=0.6, title="Temperature Distribution at Observation Time")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.histogram(filtered, x="Humidity", color="Location_Type", barmode="overlay",
                            opacity=0.6, title="Humidity Distribution at Observation Time")
        st.plotly_chart(fig, use_container_width=True)

    disturbance = filtered.groupby(["Disturbance", "Location_Type"]).size().reset_index(name="count")
    fig = px.bar(disturbance, x="Disturbance", y="count", color="Location_Type", barmode="group",
                 title="Disturbance Level vs Observations",
                 category_orders={"Disturbance": ["No effect on count", "Slight effect on count",
                                                   "Moderate effect on count", "Serious effect on count"]})
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    watch = filtered[filtered.PIF_Watchlist_Status == 1]
    if len(watch) == 0:
        st.info("No PIF Watchlist species in the current filter selection.")
    else:
        watch_counts = watch.groupby(["Common_Name", "Location_Type"]).size().reset_index(name="count")
        fig = px.bar(watch_counts, x="Common_Name", y="count", color="Location_Type",
                     title="PIF Watchlist Species Observations")
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, use_container_width=True)

    stewardship = filtered.groupby(["Location_Type"]).agg(
        watchlist_pct=("PIF_Watchlist_Status", lambda s: 100 * s.mean()),
        stewardship_pct=("Regional_Stewardship_Status", lambda s: 100 * s.mean()),
    ).reset_index()
    st.dataframe(stewardship.style.format({"watchlist_pct": "{:.1f}%", "stewardship_pct": "{:.1f}%"}),
                 use_container_width=True)

st.divider()
with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True)
    st.download_button("Download filtered data as CSV", filtered.to_csv(index=False),
                        file_name="filtered_bird_observations.csv")
