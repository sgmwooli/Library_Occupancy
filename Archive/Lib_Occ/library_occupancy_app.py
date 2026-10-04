import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import math
from supabase import create_client, Client


# ============================================================
# SUPABASE CONNECTION
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_PUBLISHABLE_KEY = st.secrets["SUPABASE_PUBLISHABLE_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)


# ============================================================
# STREAMLIT SETTINGS
# ============================================================

st.set_page_config(layout="wide")


# ============================================================
# LOAD DATA FROM SUPABASE
# ============================================================

@st.cache_data(ttl=60)
def load_data():

    response_data = []

    start = 0
    batch_size = 1000

    while True:

        response = (
            supabase
            .table("occupancy")
            .select(
                "timestamp, sj_occ, sj_cap, hc_occ, hc_cap"
            )
            .order("timestamp", desc=False)
            .range(start, start + batch_size - 1)
            .execute()
        )

        batch = response.data

        if not batch:
            break

        response_data.extend(batch)

        if len(batch) < batch_size:
            break

        start += batch_size

    if not response_data:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "sj_occ",
                "sj_cap",
                "hc_occ",
                "hc_cap"
            ]
        )

    df = pd.DataFrame(response_data)

    # Convert UTC timestamps from Supabase to UK local time
    df["timestamp"] = (
        pd.to_datetime(df["timestamp"], utc=True)
        .dt.tz_convert("Europe/London")
    )

    return df


df = load_data()


# ============================================================
# CHECK THAT DATA EXISTS
# ============================================================

if df.empty:
    st.error("No occupancy data is currently available.")
    st.stop()


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

latest = df.iloc[-1]

page = st.sidebar.radio(
    "Navigation",
    [
        "Live Dashboard",
        "Historical Lookup"
    ]
)


# ============================================================
# PAGE 1 — LIVE DASHBOARD
# ============================================================

if page == "Live Dashboard":

    st.title("📚 Library Occupancy")

    # Latest data
    sj_pct = latest["sj_occ"] / latest["sj_cap"] * 100
    hc_pct = latest["hc_occ"] / latest["hc_cap"] * 100

    # Prevent NaN values from being passed to progress()
    if math.isnan(sj_pct):
        sj_pct = 0.0

    if math.isnan(hc_pct):
        hc_pct = 0.0

    # --------------------------------------------------------
    # Latest timestamp
    # --------------------------------------------------------

    latest_time = latest["timestamp"].strftime("%H:%M:%S")

    st.caption(
        f"Latest data: {latest_time}"
    )

    # --------------------------------------------------------
    # Library occupancy
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    col1.title("**Sydney Jones**")
    col1.header(f"{sj_pct:.1f}%")
    col1.progress(sj_pct / 100)
    col1.text(
        f"{latest['sj_occ']:.0f}/{latest['sj_cap']:.0f}"
    )
    col1.text(
        f"Empty Seats: "
        f"{latest['sj_cap'] - latest['sj_occ']:.0f}"
    )

    col2.title("**Harold Cohen**")
    col2.header(f"{hc_pct:.1f}%")
    col2.progress(hc_pct / 100)
    col2.text(
        f"{latest['hc_occ']:.0f}/{latest['hc_cap']:.0f}"
    )
    col2.text(
        f"Empty Seats: "
        f"{latest['hc_cap'] - latest['hc_occ']:.0f}"
    )

    # --------------------------------------------------------
    # Occupancy graph
    # --------------------------------------------------------

    st.subheader("Occupancy Over Time")

    time_range = st.radio(
        "Select time range",
        [
            "Today",
            "Last 24 Hours",
            "Last 7 Days",
            "All Time",
            "Custom"
        ],
        horizontal=True
    )

    # --------------------------------------------------------
    # Time filtering
    # --------------------------------------------------------

    if time_range == "Today":

        # Start of today in UK time
        start_of_today = (
            latest["timestamp"]
            .normalize()
        )

        filtered = df[
            df["timestamp"] >= start_of_today
        ]

    elif time_range == "Last 24 Hours":

        filtered = df[
            df["timestamp"] >
            latest["timestamp"] - pd.Timedelta(hours=24)
        ]

    elif time_range == "Last 7 Days":

        filtered = df[
            df["timestamp"] >
            latest["timestamp"] - pd.Timedelta(days=7)
        ]

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

        # Streamlit returns naive datetimes.
        # Convert them to UK-localised timestamps.

        start_dt = pd.Timestamp(start_dt)

        end_dt = pd.Timestamp(end_dt)

        if start_dt.tzinfo is None:
            start_dt = start_dt.tz_localize(
                "Europe/London"
            )

        else:
            start_dt = start_dt.tz_convert(
                "Europe/London"
            )

        if end_dt.tzinfo is None:
            end_dt = end_dt.tz_localize(
                "Europe/London"
            )

        else:
            end_dt = end_dt.tz_convert(
                "Europe/London"
            )

        filtered = df[
            (df["timestamp"] >= start_dt) &
            (df["timestamp"] <= end_dt)
        ]

    else:

        filtered = df


    # --------------------------------------------------------
    # Calculate percentages
    # --------------------------------------------------------

    filtered = filtered.copy()

    filtered["sj_pct"] = (
        filtered["sj_occ"] /
        filtered["sj_cap"] *
        100
    )

    filtered["hc_pct"] = (
        filtered["hc_occ"] /
        filtered["hc_cap"] *
        100
    )


    # --------------------------------------------------------
    # Prepare graph
    # --------------------------------------------------------

    df2 = filtered.set_index("timestamp")[
        ["sj_pct", "hc_pct"]
    ]


    # Don't try to calculate a time span from an empty dataset
    if not df2.empty:

        time_span = (
            df2.index.max() -
            df2.index.min()
        )

        if time_span > pd.Timedelta(days=1):

            df2.index = df2.index.strftime(
                "%m-%d %H:%M"
            )

        else:

            df2.index = df2.index.strftime(
                "%H:%M"
            )


    df2 = df2.rename(
        columns={
            "sj_pct": "Sydney Jones",
            "hc_pct": "Harold Cohen"
        }
    )


    # --------------------------------------------------------
    # Display graph
    # --------------------------------------------------------

    st.line_chart(
        df2,
        x_label=["Timestamp"],
        y_label="Occupancy (%)",
        color=["#905cb5", "#b3c8c9"]
    )


# ============================================================
# PAGE 2 — HISTORICAL LOOKUP
# ============================================================

elif page == "Historical Lookup":

    st.title("🔍 Historical Lookup")

    selected_time = st.datetime_input(
        "Select date & time"
    )

    # Convert Streamlit's naive datetime into
    # a UK-localised timestamp.

    selected_time = pd.Timestamp(selected_time)

    if selected_time.tzinfo is None:

        selected_time = selected_time.tz_localize(
            "Europe/London"
        )

    else:

        selected_time = selected_time.tz_convert(
            "Europe/London"
        )


    # --------------------------------------------------------
    # Find closest timestamp
    # --------------------------------------------------------

    df["time_diff"] = abs(
        df["timestamp"] - selected_time
    )

    closest = df.loc[
        df["time_diff"].idxmin()
    ]


    # --------------------------------------------------------
    # Calculate occupancy
    # --------------------------------------------------------

    sj_pct = (
        closest["sj_occ"] /
        closest["sj_cap"] *
        100
    )

    hc_pct = (
        closest["hc_occ"] /
        closest["hc_cap"] *
        100
    )


    # --------------------------------------------------------
    # Display timestamp
    # --------------------------------------------------------

    closest_time = closest["timestamp"].strftime(
        "%d-%m-%Y %H:%M"
    )

    st.write(
        f"Closest data point: {closest_time}"
    )


    # --------------------------------------------------------
    # Display occupancy
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    col1.metric(
        "Sydney Jones",
        f"{sj_pct:.1f}%"
    )

    col2.metric(
        "Harold Cohen",
        f"{hc_pct:.1f}%"
    )