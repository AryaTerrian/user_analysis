# streamlit_app.py ───────────────────────────────────────────────
"""
Match Bingo sample data explorer
- Upload either .xlsx or .csv
- Pick the analysis “as-of” date & churn cut-off
"""

from pathlib import Path
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


BRAND_PALETTE = ["#FF2E9E", "#FDA549", "#8DC63F", "#22A9E1"]
BRAND_PINK    = "#FF2E9E"


def read_data_and_prepare(file) -> pd.DataFrame:
    """Read csv or excel into DataFrame and create lifetime metrics."""
    ext = Path(file.name).suffix.lower()
    df  = (pd.read_csv if ext == ".csv" else pd.read_excel)(file)

    df["date_joined"]     = pd.to_datetime(df["date_joined"])
    df["last_login_date"] = pd.to_datetime(df["last_login_date"])

    today = st.session_state["as_of_ts"]
    df["lifetime_days"] = (today - df["date_joined"]).dt.days.clip(lower=1)
    df["lifetime_months"] = df["lifetime_days"] / 30.0
    df["monthly_revenue"] = df["total_deposit"] / df["lifetime_months"]

    return df


def calculate_avg_clv(df: pd.DataFrame) -> float:
    """Average CLV = Avg Monthly Revenue per Customer×Avg Customer Lifetime"""
    return df['monthly_revenue'].mean() * df['cust_lifetime_months'].mean()


def tag_churn(df: pd.DataFrame, cut_off: int) -> pd.DataFrame:
    limit = st.session_state["as_of_ts"] - pd.Timedelta(days=cut_off)
    df["churned"] = df["last_login_date"] < limit
    return df


def quartile_summary(df: pd.DataFrame) -> pd.DataFrame:
    df["games_quartile"] = pd.qcut(
        df["total_games_played"], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop"
    )
    return (
        df.groupby("games_quartile", observed=True)["total_deposit"]
          .mean()
          .reindex(["Q1", "Q2", "Q3", "Q4"])
    )


# Streamlit layout
st.set_page_config(page_title="Match Bingo user analysis",
                   page_icon="🎰",
                   layout="centered")

st.sidebar.header("Controls")
uploaded_file = st.sidebar.file_uploader("Upload user CSV or XLSX", type=["csv", "xlsx"])

st.sidebar.markdown("**Analysis date** (freeze numbers)")
as_of = st.sidebar.date_input("As-of", value=date(2025, 7, 4))
st.sidebar.markdown("**Churn cut-off** (days since last login)")
cutoff_days = st.sidebar.slider("Days", min_value=7, max_value=90, value=30, step=1)

st.session_state["as_of_ts"] = pd.Timestamp(as_of)


st.title("🎯 Match Bingo user analysis")

if not uploaded_file:
    st.info("⬅️ Upload the provided sample .xlsx/.csv to begin.")
    st.stop()

df = read_data_and_prepare(uploaded_file)
df = tag_churn(df, cutoff_days)
avg_clv = calculate_avg_clv(df)
q_deposits = quartile_summary(df)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Cohort size", len(df))
    st.caption(
        'Total numbser of user in this sample dataset'
    )

with c2:
    st.metric("Avg. CLV (£)", f"{avg_clv:,.0f}")
    st.caption(
        "Average customer-lifetime value so far — Avg Monthly Revenue per Customer×Avg Customer Lifetime"
        "i.e. the cash a typical player has deposited up to today."

    )

inactive = df["churned"].sum()
with c3:
    st.metric("Inactive players", f"{inactive} / {len(df)}")
    st.caption(
        f"Using **{cutoff_days}-day** inactivity as the cut-off, "
        f"**{inactive} of {len(df)}** players (≈ {inactive/len(df):.0%}) "
        "are dormant. That’s healthy for now, but we should track it over time."
    )

st.divider()

st.subheader("Engagement vs. Spend")
fig2, ax2 = plt.subplots()
ax2.bar(q_deposits.index, q_deposits.values, color=BRAND_PALETTE)
ax2.set_xlabel("Games-played quartile"); ax2.set_ylabel("Average deposit (£)")
st.pyplot(fig2)

st.caption(
        "The bar-chart above shows that spend rises sharply with games played—"
        "players in the top quartile (Q4) deposit far more than the rest. This shows that highly engaged players have "
        "a tendency to put more money into the platform."
    )

# Descriptive table
with st.expander("Field summary (describe)"):
    st.dataframe(df.describe(include="all").T.round(2))

# Raw data
with st.expander("Raw data"):
    st.dataframe(df)
