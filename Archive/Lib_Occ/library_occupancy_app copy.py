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
# HELPER FUNCTIONS
# ============================================================

def convert_timestamps(df):

    if not df.empty:

        df["timestamp"] = (
            pd.to_datetime(
                df["timestamp"],
                utc=True
            )
            .dt.tz_convert("Europe/London")
        )

    return df


def create_dataframe(data):

    if not data:

        return pd.DataFrame(
            columns=[
                "timestamp",
                "sj_occ",
                "sj_cap",
                "hc_occ",
                "hc_cap"
            ]
        )

    df = pd.DataFrame(data)

    return convert_timestamps(df)


# ============================================================
# GET LATEST RECORD
# ============================================================

@st.cache_data(ttl=60)
def load_latest():

    response = (
        supabase
        .table("occupancy")
        .select(
            "timestamp, sj_occ, sj_cap, hc_occ, hc_cap"
        )
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )

    return create_dataframe(response.data)


# ============================================================
# LOAD DATA BETWEEN TWO TIMESTAMPS
# ============================================================

@st.cache_data(ttl=60)
def load_range(start_time, end_time):

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
            .gte(
                "timestamp",
                start_time.isoformat()
            )
            .lte(
                "timestamp",
                end_time.isoformat()
            )
            .order("timestamp", desc=False)
            .range(
                start,
                start + batch_size - 1
            )
            .execute()
        )

        batch = response.data

        if not batch:
            break

        response_data.extend(batch)

        if len(batch) < batch_size:
            break

        start += batch_size

    return create_dataframe(response_data)


# ============================================================
# LOAD ENTIRE DATABASE
# ============================================================

@st.cache_data(ttl=60)
def load_all_data():

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
            .range(
                start,
                start + batch_size - 1
            )
            .execute()
        )

        batch = response.data

        if not batch:
            break

        response_data.extend(batch)

        if len(batch) < batch_size:
            break

        start += batch_size

    return create_dataframe(response_data)


# ============================================================
# FIND CLOSEST HISTORICAL RECORD
# ============================================================

@st.cache_data(ttl=60)
def load_closest_records(selected_time):

    # --------------------------------------------------------
    # Record immediately before selected time
    # --------------------------------------------------------

    before_response = (
        supabase
        .table("occupancy")
        .select(
            "timestamp, sj_occ, sj_cap, hc_occ, hc_cap"
        )
        .lte(
            "timestamp",
            selected_time.isoformat()
        )
        .order(
            "timestamp",
            desc=True
        )
        .limit(1)
        .execute()
    )

    # --------------------------------------------------------
    # Record immediately after selected time
    # --------------------------------------------------------

    after_response = (
        supabase
        .table("occupancy")
        .select(
            "timestamp, sj_occ, sj_cap, hc_occ, hc_cap"
        )
        .gte(
            "timestamp",
            selected_time.isoformat()
        )
        .order(
            "timestamp",
            desc=False
        )
        .limit(1)
        .execute()
    )

    data = (
        before_response.data +
        after_response.data
    )

    return create_dataframe(data)


# ============================================================
# CHECK THAT DATA EXISTS
# ============================================================

latest_df = load_latest()

if latest_df.empty:

    st.error(
        "No occupancy data is currently available."
    )

    st.stop()


latest = latest_df.iloc[0]


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

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

    # --------------------------------------------------------
    # Latest data
    # --------------------------------------------------------

    sj_pct = (
        latest["sj_occ"] /
        latest["sj_cap"] *
        100
    )

    hc_pct = (
        latest["hc_occ"] /
        latest["hc_cap"] *
        100
    )

    # Prevent NaN values from being passed to progress()

    if math.isnan(sj_pct):
        sj_pct = 0.0

    if math.isnan(hc_pct):
        hc_pct = 0.0


    # --------------------------------------------------------
    # Latest timestamp
    # --------------------------------------------------------

    latest_time = latest["timestamp"].strftime(
        "%H:%M:%S"
    )

    st.caption(
        f"Latest data: {latest_time}"
    )


    # --------------------------------------------------------
    # Library occupancy
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    col1.title("**Sydney Jones**")

    col1.header(
        f"{sj_pct:.1f}%"
    )

    col1.progress(
        sj_pct / 100
    )

    col1.text(
        f"{latest['sj_occ']:.0f}/"
        f"{latest['sj_cap']:.0f}"
    )

    col1.text(
        f"Empty Seats: "
        f"{latest['sj_cap'] - latest['sj_occ']:.0f}"
    )


    col2.title("**Harold Cohen**")

    col2.header(
        f"{hc_pct:.1f}%"
    )

    col2.progress(
        hc_pct / 100
    )

    col2.text(
        f"{latest['hc_occ']:.0f}/"
        f"{latest['hc_cap']:.0f}"
    )

    col2.text(
        f"Empty Seats: "
        f"{latest['hc_cap'] - latest['hc_occ']:.0f}"
    )


    # --------------------------------------------------------
    # Occupancy graph
    # --------------------------------------------------------

    st.subheader(
        "Occupancy Over Time"
    )

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


    # ========================================================
    # DETERMINE REQUIRED DATA RANGE
    # ========================================================

    if time_range == "Today":

        start_time = latest["timestamp"].normalize()

        end_time = latest["timestamp"]

        filtered = load_range(
            start_time,
            end_time
        )


    elif time_range == "Last 24 Hours":

        start_time = (
            latest["timestamp"] -
            pd.Timedelta(hours=24)
        )

        end_time = latest["timestamp"]

        filtered = load_range(
            start_time,
            end_time
        )


    elif time_range == "Last 7 Days":

        start_time = (
            latest["timestamp"] -
            pd.Timedelta(days=7)
        )

        end_time = latest["timestamp"]

        filtered = load_range(
            start_time,
            end_time
        )


    elif time_range == "Custom":

        col_start, col_end = st.columns(2)

        # Default to the most recent 7 days
        default_start = (
            latest["timestamp"] -
            pd.Timedelta(days=7)
        )

        default_end = latest["timestamp"]


        with col_start:

            start_dt = st.datetime_input(
                "Start date & time",
                value=default_start.to_pydatetime()
            )


        with col_end:

            end_dt = st.datetime_input(
                "End date & time",
                value=default_end.to_pydatetime()
            )


        # ----------------------------------------------------
        # Convert Streamlit datetime values to UK timezone
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # Check that the range is valid
        # ----------------------------------------------------

        if start_dt >= end_dt:

            st.error(
                "The start date/time must be "
                "before the end date/time."
            )

            st.stop()


        filtered = load_range(
            start_dt,
            end_dt
        )


    else:

        # ----------------------------------------------------
        # All Time
        # ----------------------------------------------------

        filtered = load_all_data()


    # ========================================================
    # CALCULATE PERCENTAGES
    # ========================================================

    filtered = filtered.copy()


    if filtered.empty:

        st.warning(
            "No occupancy data exists for "
            "the selected time range."
        )

        st.stop()


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


    # ========================================================
    # PREPARE GRAPH
    # ========================================================

    df2 = filtered.set_index(
        "timestamp"
    )[
        ["sj_pct", "hc_pct"]
    ]


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


    # ========================================================
    # DISPLAY GRAPH
    # ========================================================

    st.line_chart(
        df2,
        x_label=["Timestamp"],
        y_label="Occupancy (%)",
        color=[
            "#905cb5",
            "#b3c8c9"
        ]
    )


# ============================================================
# PAGE 2 — HISTORICAL LOOKUP
# ============================================================

elif page == "Historical Lookup":

    st.title(
        "🔍 Historical Lookup"
    )


    # --------------------------------------------------------
    # Select time
    # --------------------------------------------------------

    selected_time = st.datetime_input(
        "Select date & time"
    )


    # --------------------------------------------------------
    # Convert to UK timezone
    # --------------------------------------------------------

    selected_time = pd.Timestamp(
        selected_time
    )


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

    candidates = load_closest_records(
        selected_time
    )


    if candidates.empty:

        st.warning(
            "No occupancy data could be found."
        )

        st.stop()


    # Calculate difference between selected
    # time and candidate records

    candidates["time_diff"] = abs(
        candidates["timestamp"] -
        selected_time
    )


    closest = candidates.loc[
        candidates["time_diff"].idxmin()
    ]


    # ========================================================
    # CALCULATE OCCUPANCY
    # ========================================================

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


    # ========================================================
    # DISPLAY TIMESTAMP
    # ========================================================

    closest_time = (
        closest["timestamp"]
        .strftime("%d-%m-%Y %H:%M")
    )


    st.write(
        f"Closest data point: {closest_time}"
    )


    # ========================================================
    # DISPLAY OCCUPANCY
    # ========================================================

    col1, col2 = st.columns(2)


    col1.metric(
        "Sydney Jones",
        f"{sj_pct:.1f}%"
    )


    col2.metric(
        "Harold Cohen",
        f"{hc_pct:.1f}%"
    )