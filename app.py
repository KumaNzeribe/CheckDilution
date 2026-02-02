import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Dilution Risk Checker", layout="centered")
st.title("📊 Stock Dilution Risk Checker")

# -----------------------------
# Functions
# -----------------------------
@st.cache_data(ttl=3600)
def fetch_shares_outstanding(ticker: str):
    """Fetch historical shares outstanding (best-effort)"""
    stock = yf.Ticker(ticker)
    shares_data = None

    try:
        # Attempt quarterly financials
        shares_data = stock.quarterly_financials.T  # transpose: dates as rows
        shares_data = shares_data.rename(columns=lambda x: x.replace(" ", "_"))

        # fallback: info['sharesOutstanding'] (current only)
        current_shares = stock.info.get("sharesOutstanding")
        if current_shares:
            shares_data["SharesOutstanding"] = current_shares

        if shares_data.empty:
            return None

        return shares_data

    except Exception as e:
        st.error(f"Error fetching shares: {e}")
        return None


def compute_dilution(shares_df: pd.DataFrame):
    """Compute period-to-period dilution % and rating"""
    if shares_df is None or "SharesOutstanding" not in shares_df.columns:
        return None, "⚪ N/A"

    # Sort by date ascending
    shares_df = shares_df.sort_index()

    # Compute % change
    shares_df["DilutionPct"] = shares_df["SharesOutstanding"].pct_change() * 100

    last_dilution = shares_df["DilutionPct"].iloc[-1]

    # Assign risk rating
    if last_dilution is None or pd.isna(last_dilution):
        rating = "⚪ N/A"
    elif last_dilution > 10:
        rating = "🔴 High"
    elif last_dilution > 2:
        rating = "🟡 Moderate"
    else:
        rating = "🟢 Stable"

    return last_dilution, rating


# -----------------------------
# UI
# -----------------------------
ticker = st.text_input("Enter stock ticker (e.g. AAPL, MSFT, KO)").upper().strip()
analyze = st.button("Check Dilution Risk")

if analyze and ticker:
    with st.spinner("Fetching shares data..."):
        shares_df = fetch_shares_outstanding(ticker)
        time.sleep(0.2)  # small delay for cache

    if shares_df is None or shares_df.empty:
        st.error("Shares outstanding data unavailable for this ticker.")
        st.stop()

    st.subheader("Shares Outstanding Data (last 5 periods)")
    st.dataframe(shares_df.tail(5))

    last_dilution, rating = compute_dilution(shares_df)

    if last_dilution is not None:
        st.metric("Last Period Dilution (%)", f"{last_dilution:.2f}%")
    st.markdown(f"**Dilution Risk Rating:** {rating}")
