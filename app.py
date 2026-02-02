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
    try:
        stock = yf.Ticker(ticker)

        # Attempt quarterly financials
        shares_df = pd.DataFrame()

        # First, try stock info (current shares only)
        current_shares = stock.info.get("sharesOutstanding")
        if current_shares:
            shares_df = pd.DataFrame({
                "SharesOutstanding": [current_shares]
            }, index=[pd.Timestamp("Today")])

        # Optionally, try history of quarterly shares (some tickers may provide)
        try:
            hist = stock.quarterly_financials.T
            if not hist.empty:
                hist = hist.rename(columns=lambda x: x.replace(" ", "_"))
                if "SharesOutstanding" in hist.columns:
                    shares_df = hist[["SharesOutstanding"]]
        except Exception:
            pass

        if shares_df.empty:
            return None

        return shares_df.sort_index()

    except Exception as e:
        st.error(f"Error fetching shares for {ticker}: {e}")
        return None


def compute_dilution(shares_df: pd.DataFrame):
    """Compute period-to-period dilution % and rating"""
    if shares_df is None or "SharesOutstanding" not in shares_df.columns:
        return None, "⚪ N/A"

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
    with st.spinner(f"Fetching shares data for {ticker}..."):
        shares_df = fetch_shares_outstanding(ticker)
        time.sleep(0.2)  # small delay for cache

    if shares_df is None or shares_df.empty:
        st.error("Shares outstanding data unavailable for this ticker.")
    else:
        st.subheader("Shares Outstanding Data (last 5 periods)")
        st.dataframe(shares_df.tail(5))

        last_dilution, rating = compute_dilution(shares_df)

        if last_dilution is not None:
            st.metric("Last Period Dilution (%)", f"{last_dilution:.2f}%")
        st.markdown(f"**Dilution Risk Rating:** {rating}")

        # Optional: line chart of dilution trend
        if "DilutionPct" in shares_df.columns:
            st.line_chart(shares_df["DilutionPct"].dropna(), height=250)
