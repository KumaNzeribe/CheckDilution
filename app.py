import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Dilution Risk Checker", layout="centered")
st.title("Stock Dilution Risk Checker")

# ----------------------------
# Function to fetch shares
# ----------------------------
@st.cache_data(ttl=3600)
def load_shares_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        shares_out = info.get("sharesOutstanding")
        return shares_out
    except Exception:
        return None

# ----------------------------
# UI
# ----------------------------
ticker = st.text_input("Enter stock ticker (e.g. AAPL, MSFT)").upper().strip()
check = st.button("Check Dilution")

if check and ticker:
    st.info("Fetching data...")
    shares_out = load_shares_data(ticker)
    
    if shares_out is None:
        st.error("Unable to fetch share data. This ticker may not exist or Yahoo Finance data unavailable.")
    else:
        st.success(f"**Current Outstanding Shares:** {shares_out:,}")
        st.info("Historical dilution data not available. This app currently only reports current shares outstanding.")

