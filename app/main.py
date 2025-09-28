import streamlit as st
import sys, os

st.sidebar.markdown("### 🔧 Debug")
st.sidebar.write("Python:", sys.version.split()[0])
st.sidebar.write("CWD:", os.getcwd())
st.sidebar.write("Repo files:", sorted(os.listdir(".")))
st.sidebar.write("app/ files:", sorted(os.listdir("./app")) if os.path.isdir("./app") else "no app/")

# verify yfinance import works on Cloud
try:
    import yfinance as yf  # noqa: F401
    st.sidebar.success("yfinance import ✅")
except Exception as e:
    st.sidebar.error(f"yfinance import ❌: {e}")
