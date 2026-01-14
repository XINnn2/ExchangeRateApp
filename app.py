import streamlit as st
import pandas as pd
import pickle
import plotly.graph_objects as go

# ==============================
# UI CONFIGURATION
# ==============================
st.set_page_config(
    page_title="MedFX Navigator",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
.metric-container {
    background-color: #f8f9fa;
    padding: 12px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# DATA & MODEL LOADING
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("exchange-rates-new.csv")
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    df = df.set_index("date")
    return df

@st.cache_resource
def load_model():
    with open("holt_model.pkl", "rb") as f:
        return pickle.load(f)

df = load_data()
model = load_model()

# ==============================
# SIDEBAR NAVIGATOR
# ==============================
st.sidebar.markdown("## 🏥 **MedFX Navigator**")
st.sidebar.caption("Medical Tourism Exchange Intelligence Platform")
st.sidebar.markdown("---")

horizon = st.sidebar.slider("📆 Forecast Horizon (Days)", 1, 30, 7)

active_page = st.sidebar.selectbox(
    "Select Module",
    [
        "📊 Market Insights",
        "💰 Budget & Hospital Planner",
        "🌿 Recovery & Travel"
    ]
)

st.sidebar.info(
    "1️⃣ Review exchange trends\n\n"
    "2️⃣ Plan your medical budget\n\n"
    "3️⃣ Prepare recovery & travel safely"
)

# ==============================
# FORECAST PREPARATION (HOLT)
# ==============================
train = df["USD"].iloc[:-216]
test = df["USD"].iloc[-216:]

test_forecast = model.forecast(steps=len(test))

last_date = df.index.max()
future_dates = pd.date_range(
    start=last_date + pd.Timedelta(days=1),
    periods=horizon,
    freq="D"
)

future_forecast = model.forecast(steps=horizon)

# ==============================
# SHARED VARIABLES
# ==============================
current_rate = df["USD"].iloc[-1]
avg_future = future_forecast.mean()

# ==============================
# PAGE 1: MARKET INSIGHTS
# ==============================
if active_page == "📊 Market Insights":
    st.title("📊 Exchange Rate & Action Plan")

    col1, col2 = st.columns(2)
    col1.metric("💱 Current USD/MYR", f"{current_rate:.4f}")
    col2.metric(
        f"📅 {horizon}-Day Avg Forecast",
        f"{avg_future:.4f}",
        delta=f"{avg_future - current_rate:.4f}",
        delta_color="inverse"
    )

    st.subheader("💡 Action Plan for Patients")
    if avg_future > current_rate:
        st.success(
            "**Highly Favorable Timing**\n"
            "USD is expected to strengthen, increasing purchasing power "
            "for medical procedures in Malaysia."
        )
    else:
        st.warning(
            "**Monitor the Market**\n"
            "Rates appear stable. Consider flexibility if treatment timing allows."
        )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
    x=train.index,
    y=train.values,
    name="Historical Data"
))


    fig.add_trace(go.Scatter(
        x=test.index,
        y=test.values,
        name="Testing Data (Actual)"
    ))

    fig.add_trace(go.Scatter(
        x=test.index,
        y=test_forecast,
        name="Testing Forecast",
        line=dict(dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=future_dates,
        y=future_forecast,
        name="Future Forecast",
        line=dict(width=4)
    ))

    fig.update_layout(
        title="Holt (Double Exponential Smoothing) Exchange Rate Forecast",
        xaxis_title="Date",
        yaxis_title="USD/MYR"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# PAGE 2: BUDGET & HOSPITAL PLANNER
# ==============================
elif active_page == "💰 Budget & Hospital Planner":
    st.title("💰 Budget & Hospital Planner")

    st.markdown("---")
    st.markdown("### 🧮 Medical Cost Conversion")

    user_cost_myr = st.number_input(
        "Enter estimated treatment cost (MYR):",
        min_value=100,
        value=20000
    )

    calc_data = {
        "Scenario": ["Pay Today", f"Pay in {horizon} Days"],
        "Exchange Rate": [current_rate, avg_future],
        "Estimated Cost (USD)": [
            user_cost_myr / current_rate,
            user_cost_myr / avg_future
        ]
    }

    calc_df = pd.DataFrame(calc_data)

    st.table(calc_df.style.format({
        "Exchange Rate": "{:.4f}",
        "Estimated Cost (USD)": "${:,.2f}"
    }))

    # ----- Procedure Cost Analysis -----
    st.markdown("#### 📑 Standard Procedure Cost Analysis")

    procedures = {
        "Procedure": [
            "Health Screening",
            "Dental Implant",
            "Knee Replacement",
            "LASIK Eye Surgery"
        ],
        "Cost_MYR": [2000, 8000, 45000, 7500]
    }

    proc_df = pd.DataFrame(procedures)
    proc_df["USD (Current)"] = proc_df["Cost_MYR"] / current_rate
    proc_df["USD (Forecasted)"] = proc_df["Cost_MYR"] / avg_future
    proc_df["Difference"] = (
        proc_df["USD (Current)"] - proc_df["USD (Forecasted)"]
    )

    st.table(proc_df.style.format({
        "Cost_MYR": "{:,.0f} MYR",
        "USD (Current)": "${:,.2f}",
        "USD (Forecasted)": "${:,.2f}",
        "Difference": "${:,.2f}"
    }))

    # ----- Savings -----
    savings = (
        calc_df.loc[0, "Estimated Cost (USD)"]
        - calc_df.loc[1, "Estimated Cost (USD)"]
    )

    if savings > 0:
        st.success(f"💡 Potential savings: **${savings:,.2f} USD**")
    else:
        st.info("ℹ️ No significant exchange advantage detected.")

    st.markdown("---")

    # ----- Hospital Recommendation -----
    st.subheader("📍 Find Accredited Hospitals")

    location = st.selectbox(
        "Where are you planning to visit?",
        ["Kuala Lumpur", "Penang", "Johor Bahru", "Melaka"]
    )

    hospitals = {
        "Kuala Lumpur": [
            "Gleneagles Hospital",
            "Prince Court Medical Centre",
            "Sunway Medical Centre"
        ],
        "Penang": [
            "Island Hospital",
            "Gleneagles Penang",
            "Loh Guan Lye Specialists Centre"
        ],
        "Johor Bahru": [
            "KPJ Johor Specialist Hospital",
            "Columbia Asia Hospital"
        ],
        "Melaka": [
            "Mahkota Medical Centre"
        ]
    }

    st.write(f"Top JCI-Accredited hospitals in **{location}**:")
    for hosp in hospitals[location]:
        st.info(f"🏢 {hosp}")

    st.caption(
        "Hospital listings are informational and do not imply endorsement."
    )

# ==============================
# PAGE 3: RECOVERY & TRAVEL
# ==============================
elif active_page == "🌿 Recovery & Travel":
    st.title("🌿 Recovery & Wellness Planning")
    st.markdown("### 🩺 Post-Treatment Lifestyle Support")

    treatment = st.selectbox(
        "Select your treatment category:",
        [
            "Cardiac/Major Surgery",
            "Orthopedic (Joint/Knee)",
            "Cosmetic/Dental",
            "General Wellness"
        ]
    )

    st.subheader("🧘 Recommended Activities")
    if treatment == "Orthopedic (Joint/Knee)":
        st.write("- Short flat walks (parks, gardens)")
        st.write("- Museums with elevator access")
    elif treatment == "Cardiac/Major Surgery":
        st.write("- Quiet indoor activities")
        st.write("- Gentle breathing exercises")
    else:
        st.write("- Light cultural tours")
        st.write("- Wellness activities (doctor-approved)")

    st.subheader("🥗 Nutrition Guidance")
    if treatment == "Cardiac/Major Surgery":
        st.write("- Low-sodium meals")
        st.write("- Heart-healthy fats")
    elif treatment == "Orthopedic (Joint/Knee)":
        st.write("- Protein-rich foods")
        st.write("- Anti-inflammatory nutrients")
    else:
        st.write("- Adequate hydration")
        st.write("- Immune-supportive nutrition")

    risk_map = {
        "Cardiac/Major Surgery": "🔴 High caution required",
        "Orthopedic (Joint/Knee)": "🟡 Moderate caution required",
        "Cosmetic/Dental": "🟢 Low risk activities",
        "General Wellness": "🟢 Low risk activities"
    }

    st.warning(f"⚠️ Recovery Risk Level: **{risk_map[treatment]}**")
    st.info(
        "Always follow hospital discharge instructions "
        "and consult your doctor."
    )

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(
    "MedFX Navigator © 2026 | Educational Decision-Support Tool | "
    "Not a substitute for medical or financial advice"
)

