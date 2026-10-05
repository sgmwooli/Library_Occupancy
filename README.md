# 📚 University of Liverpool Library Occupancy Dashboard
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://library-occupancy.streamlit.app/)

A real-time library occupancy dashboard for the University of Liverpool, displaying current and historical occupancy data for the **Sydney Jones Library** and **Harold Cohen Library**.

The application retrieves occupancy data automatically, stores it in a Supabase PostgreSQL database, and presents the data through an interactive Streamlit dashboard.

**Live application:**  
https://library-occupancy.streamlit.app/

---

## Overview

The University of Liverpool provides live occupancy data through its library occupancy API. This project collects that data automatically and uses it to provide:

- Current occupancy for both libraries
- Percentage occupancy
- Number of occupied and available seats
- Occupancy trends over time
- Data for the current day
- The previous 24 hours
- The previous 7 days
- Custom date/time ranges
- All available historical data
- Historical lookup for a specific date and time

The database currently contains both continuously collected live data and historical data imported from an earlier local data collection system.

---

## Dashboard

The application has two main sections.

### Live Dashboard

The Live Dashboard displays the latest available occupancy data for both libraries.

For each library it shows:

- Occupancy percentage
- Occupied seats / total capacity
- Number of empty seats
- Time of the latest measurement

It also provides an interactive graph showing occupancy over time.

Available graph ranges are:

- **Today**
- **Last 24 Hours**
- **Last 7 Days**
- **All Time**
- **Custom**

### Historical Lookup

The Historical Lookup page allows a user to select a specific date and time.

The application then identifies the occupancy measurement closest to the requested time and displays the corresponding occupancy percentages for both libraries.

---

## Architecture

The project uses a serverless architecture so that data collection does not depend on a personal computer being left running.

```text
University of Liverpool
        │
        │ Occupancy API
        ▼
Supabase Edge Function
        │
        │ Every minute
        ▼
Supabase PostgreSQL
        │
        │ Query via API
        ▼
Streamlit Community Cloud
        │
        ▼
Interactive Dashboard
```

### Data collection

A Supabase Edge Function named `collect-occupancy` retrieves the latest occupancy data from the University of Liverpool API.

Supabase Cron executes the function automatically every minute.

The resulting data is stored in a PostgreSQL table.

This means the data collection system continues to operate without requiring a local Mac, Raspberry Pi, or other computer to remain switched on.

---

## Database

Occupancy data is stored in a Supabase PostgreSQL table called `occupancy`.

The table contains:

| Column | Type | Description |
|---|---|---|
| `id` | `bigint` | Automatically generated unique identifier |
| `timestamp` | `timestamptz` | Time of the measurement |
| `sj_occ` | `integer` | Sydney Jones occupancy |
| `sj_cap` | `integer` | Sydney Jones capacity |
| `hc_occ` | `integer` | Harold Cohen occupancy |
| `hc_cap` | `integer` | Harold Cohen capacity |

Timestamps are stored as timezone-aware UTC timestamps and converted to UK local time by the Streamlit application.

---

## Efficient Data Retrieval

As historical data accumulates, downloading the entire database every time the application loads would become increasingly inefficient.

The application therefore queries only the data it requires.

| Function | Data retrieved |
|---|---|
| Current occupancy | Latest record |
| Today | Today's records |
| Last 24 Hours | Previous 24 hours |
| Last 7 Days | Previous 7 days |
| Custom range | Requested date/time range |
| Historical Lookup | Closest records to requested time |
| All Time | Entire database |

The normal dashboard therefore remains fast even as the historical database continues to grow.

Database queries are cached using Streamlit's `st.cache_data` functionality to reduce unnecessary requests.

---

## Historical Data

Before the Supabase system was implemented, occupancy data was collected locally using a Python script and stored in a CSV file.

The historical CSV data was subsequently imported into the Supabase database, allowing the dashboard to display data from both the original collection period and the new automated collection system.

This provides a continuous historical dataset rather than starting again from the date that the cloud infrastructure was introduced.

---

## Technologies

### Frontend / Dashboard

- [Streamlit](https://streamlit.io/)
- Python
- Pandas
- NumPy

### Database / Backend

- Supabase
- PostgreSQL
- Supabase Edge Functions
- Supabase Cron

### Data Source

- University of Liverpool Library Occupancy API

### Deployment

- Streamlit Community Cloud
- GitHub

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/sgmwooli/Library_Occupancy
cd library_occupancy
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it with:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Supabase credentials

Create:

```text
.streamlit/secrets.toml
```

containing:

```toml
SUPABASE_URL = "your-supabase-project-url"
SUPABASE_PUBLISHABLE_KEY = "your-supabase-publishable-key"
```

The `secrets.toml` file should **not** be committed to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

The application will then be available locally through Streamlit.

---

## Security

The Streamlit application uses the Supabase **publishable key** for database read access.

The Supabase service-role key is **not** included in the Streamlit application.

The service-role credentials required by the data collection Edge Function remain server-side and are stored securely within Supabase.

Local Streamlit secrets are excluded from version control.

---

## Project Structure

```text
library_occupancy/
│
├── app.py
├── requirements.txt
├── README.md
│
└── .streamlit/
    └── secrets.toml
```

---

## Future Improvements

Possible future additions include:

- Occupancy forecasting
- Prediction of busy periods
- Automatic identification of unusually busy periods
- Historical daily/weekly comparisons
- Average occupancy by hour and day of the week
- Comparison between libraries
- Improved data visualisation
- Automated anomaly detection
- Downloadable historical datasets
- Additional University of Liverpool libraries if data becomes available

---

## Purpose

This project was developed as an independent data analytics and software development project to demonstrate practical experience with:

- Data collection
- REST APIs
- Automated data pipelines
- Cloud databases
- SQL/PostgreSQL
- Data cleaning and transformation
- Time-series data
- Data visualisation
- Interactive dashboards
- Cloud deployment
- Serverless computing
- Python development

The project demonstrates an end-to-end data pipeline from **API → automated collection → cloud database → data processing → interactive visualisation**.
