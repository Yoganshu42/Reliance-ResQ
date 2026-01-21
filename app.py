import streamlit as st
import analysis

st.set_page_config(
    page_title="Reliance ResQ Dashboard",
    layout="wide"
)

st.title("📊 Reliance ResQ – Sales, Claims & Loss Ratio Dashboard")

# Create tabs
tab_plan, tab_brand, tab_state, tab_period, tab_prediction = st.tabs([
    "📦 Plan Type-wise Analysis",
    "🏷️ Brand-wise Analysis",
    "🗺️ State-wise Analysis",
    "⏱️ Claim Period Analysis",
    "📈 Prediction Analysis"
])

# ---------------- PLAN TAB ---------------- #
with tab_plan:
    st.subheader("📦 Plan Type-wise Metrics & Loss Ratios")
    analysis.run_dashboard(selection="plan")

# ---------------- BRAND TAB ---------------- #
with tab_brand:
    st.subheader("🏷️ Brand-wise Metrics & Loss Ratios")
    analysis.run_dashboard(selection="brand")

# ---------------- STATE TAB ---------------- #
with tab_state:
    st.subheader("🗺️ State-wise Metrics & Loss Ratios")
    analysis.run_dashboard(selection="state")

# ---------------- CLAIM PERIOD TAB ---------------- #
with tab_period:
    st.subheader("⏱️ Claim Period Analysis")
    analysis.run_dashboard(selection="period")

# ---------------- PREDICTION TAB ---------------- #
with tab_prediction:
    # st.subheader("📈 Sales & Claims Prediction")
    analysis.run_dashboard(selection="prediction")
