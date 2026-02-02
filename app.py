import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Dilution Risk Checker", layout="centered")
st.title("Stock Dilution Risk Checker")

# ----------------------------
# Function to load share data
# ----------------------------
@st.cache_data(ttl=3600)
def load_shares_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.get_info()
        
        # Attempt to get shares history
        shares_out = info.get("sharesOutstanding")
        if shares_out is None:
            return None
        
        # Try quarterly share history from financials if available
        bal_sheet = stock.balance_sheet
        if bal_sheet is not None and not bal_sheet.empty:
            # balance_sheet columns are dates
            shares_series = bal_sheet.loc["Common Stock", :] if "Common Stock" in bal_sheet.index else None
        else:
            shares_series = None

        return {
            "current": shares_out,
            "history": shares_series
        }

    except Exception as e:
        return None

# ----------------------------
# Dilution calculation
# ----------------------------
def calculate_dilution(shares_history):
    if shares_history is None or shares_history.empty:
        return None, "Data unavailable"
    
    # Take first and last available values
    first = shares_history.iloc[-1]  # oldest
    last = shares_history.iloc[0]    # newest
    if first == 0:
        return None, "Invalid data"
    
    pct_change = (last - first) / first * 100
    
    # Risk rating
    if pct_change > 5:
        rating = "🔴 High dilution risk"
    elif pct_change > 1:
        rating = "🟡 Moderate dilution risk"
    else:
        rating = "🟢 Low dilution risk"
    
    return pct_change, rating

# ----------------------------
# UI
# ----------------------------
ticker = st.text_input("Enter stock ticker (e.g. AAPL, MSFT)").upper().strip()
check = st.button("Check Dilution")

if check and ticker:
    st.info("Fetching data...")
    data = load_shares_data(ticker)
    
    if data is None:
        st.error("Unable to fetch share data. Try another ticker.")
        st.stop()
    
    current = data["current"]
    history = data["history"]
    
    st.write(f"**Current Outstanding Shares:** {current:,}")
    
    pct_change, rating = calculate_dilution(history)
    
    if pct_change is not None:
        st.write(f"**Share Change (oldest → newest):** {pct_change:+.2f}%")
    
    st.write(f"**Dilution Risk:** {rating}")
