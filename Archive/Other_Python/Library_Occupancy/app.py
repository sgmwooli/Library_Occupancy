import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import math

st.set_page_config(layout="wide")

file = "occupancy_log.csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(file, parse_dates=["timestamp"], dtype=np.float64)
    # df = pd.read_csv(file, dtype={'timestamp': np.datetime64, 
    #                               'sj_occ': 'Int64',
    #                               'sj_cap': 'Int64',
    #                               'hc_occ': 'Int64',
    #                               'hc_cap': 'Int64'})
    return df

df = load_data()

# --- Sidebar navigation ---
latest = df.iloc[-1]
page = st.sidebar.radio("Navigation", [
    f"Live Dashboard\n({str(latest['timestamp'])[11:16]})", 
    f"Historical Lookup"
    ])

# --- PAGE 1 (Live Dashboard) ---
if page == f"Live Dashboard\n({str(latest['timestamp'])[11:16]})":
    st.title("📚 Library Occupancy")


    # print(f"{latest['sj_occ']=}\n{latest['sj_cap']=}")
    # print(f"{latest['hc_occ']=}\n{latest['hc_cap']=}")
    sj_pct = latest["sj_occ"] / latest["sj_cap"] * 100
    hc_pct = latest["hc_occ"] / latest["hc_cap"] * 100

    col1, col2 = st.columns(2)

    col1.title("**Sydney Jones**")
    col1.header(f"{sj_pct:.1f}%")
    if math.isnan(sj_pct):
        sj_pct = 0.0
    col1.progress(sj_pct/100)
    col1.text(f"{latest['sj_occ']:.0f}/{latest['sj_cap']:.0f}")
    col1.text(f"Empty Seats: {latest['sj_cap']-latest['sj_occ']:.0f}")

    col2.title("**Harold Cohen**")
    col2.header(f"{hc_pct:.1f}%")
    if math.isnan(hc_pct):
        hc_pct = 0.0
    col2.progress(hc_pct/100)
    col2.text(f"{latest['hc_occ']:.0f}/{latest['hc_cap']:.0f}")
    col2.text(f"Empty Seats: {latest['hc_cap']-latest['hc_occ']:.0f}")

    st.subheader("Occupancy Over Time")

    # Time range selector (default last 24h)
    time_range = st.radio(
        "Select time range",
        ["Today", "Last 24 Hours", "Last 7 Days", "All Time", "Custom"],
        horizontal = True
    )

    # print(f"\n\n{df["timestamp"].max()=}\n{pd.Timedelta(hours=24)=}\n\n")
    if time_range == "Today":
        h, m = int(datetime.now().strftime("%H")), int(datetime.now().strftime("%M"))
        filtered = df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(hours=h, minutes=m)]
    elif time_range == "Last 24 Hours":
        filtered = df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(hours=24)]
    elif time_range == "Last 7 Days":
        filtered = df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(days=7)]
    elif time_range == "Custom":
        col_start, col_end = st.columns(2)
        with col_start:
            start_dt = st.datetime_input(
                "Start date & time",
                value=df["timestamp"].min()
            )
        with col_end:
            end_dt = st.datetime_input(
                "End date & time",
                value=df["timestamp"].max()
            )

        filtered = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]
    else:
        filtered = df

    filtered = filtered.copy()
    filtered.loc[:, "sj_pct"] = filtered["sj_occ"] / filtered["sj_cap"] * 100
    filtered.loc[:, "hc_pct"] = filtered["hc_occ"] / filtered["hc_cap"] * 100

    df2 = filtered.set_index("timestamp")[["sj_pct", "hc_pct"]]

    # Decide formatting based on time span
    time_span = df2.index.max() - df2.index.min()

    if time_span > pd.Timedelta(days=1):
        # Multi-day → show date only
        df2.index = df2.index.strftime("%m-%d %H:%M")
    else:
        # <24h → show time, but include date at midnight
        df2.index = df2.index.strftime("%H:%M")

    # df2.index = df2.index.date
    # df2 = df2.groupby(df2.index).mean()  # aggregate if multiple points per day
    df2 = df2.rename(columns={
            "sj_pct": "Sydney Jones",
            "hc_pct": "Harold Cohen"
        })
    st.line_chart(df2, 
                  x_label=["Timestamp"],
                  y_label="Occupancy (%)",
                  color=["#905cb5", "#b3c8c9"])

# --- PAGE 2 (Historical Lookup) ---
elif page == "Historical Lookup":
    st.title("🔍 Historical Lookup")

    selected_time = st.datetime_input("Select date & time")

    # Find closest timestamp
    df["time_diff"] = abs(df["timestamp"] - selected_time)
    closest = df.loc[df["time_diff"].idxmin()]

    sj_pct = closest["sj_occ"] / closest["sj_cap"] * 100
    hc_pct = closest["hc_occ"] / closest["hc_cap"] * 100

    closest_time = datetime.strptime(str(closest['timestamp']), "%Y-%m-%d %H:%M:%S.%f").strftime("%d-%m-%Y %H:%M")
    st.write(f"Closest data point: {closest_time}")

    col1, col2 = st.columns(2)
    col1.metric("Sydney Jones", f"{sj_pct:.1f}%")
    col2.metric("Harold Cohen", f"{hc_pct:.1f}%")