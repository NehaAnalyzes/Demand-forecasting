import streamlit as st
import pandas as pd
import plotly.express as px

# Authentication check
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.title("🎯 Smart Procurement Planning")
st.caption("Ministry of Power, Govt of India")

# ====== DEFINITIVE LABEL MAPS (customize as needed) =======
project_type_map = {
    "Transmissi": "Transmission Project",
    "Transmission": "Transmission Project",
    0: "Transmission Project",
    "Substation": "Substation Project",
    1: "Substation Project"
}

state_map = {
    "Gujarat": "Gujarat",
    "Maharash": "Maharashtra",
    "Assam": "Assam",
    "Tamil Nad": "Tamil Nadu",
    "Uttar Prad": "Uttar Pradesh",
    0: "Gujarat",
    1: "Maharashtra",
    2: "Assam",
    3: "Tamil Nadu",
    4: "Uttar Pradesh"
    # Add other codes/numeric values as needed!
}

# ===== DATA LOAD + COLUMN SANITIZATION =====
@st.cache_data
def load_data():
    df = pd.read_csv('hybrid_cleaned.csv')
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]  # handles whitespace and weird headers
    # Derive user-friendly fields for mapping
    project_type_base = df.columns[df.columns.str.lower().str.contains("project_ty|project_type")][0]
    state_base = df.columns[df.columns.str.lower().str.contains("state")][0]
    df['Project_Type_Full'] = df[project_type_base].map(project_type_map).fillna(df[project_type_base].astype(str))
    df['State_Full'] = df[state_base].map(state_map).fillna(df[state_base].astype(str))
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

df = load_data()

st.markdown("---")

# ======================= FILTERS =========================
st.markdown("### 🔎 Filter Procurement Data")

col1, col2 = st.columns(2)
with col1:
    states = ['All'] + sorted(df['State_Full'].dropna().unique().tolist())
    selected_state = st.selectbox("Select State", options=states)
with col2:
    project_types = ['All'] + sorted(df['Project_Type_Full'].dropna().unique().tolist())
    selected_project = st.selectbox("Select Project Type", options=project_types)

# Filter Data
filtered_df = df.copy()
if selected_state != 'All':
    filtered_df = filtered_df[filtered_df['State_Full'] == selected_state]
if selected_project != 'All':
    filtered_df = filtered_df[filtered_df['Project_Type_Full'] == selected_project]

# ========== OVERVIEW METRICS ==========
st.markdown("### 📊 Procurement Overview")
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_states = filtered_df['State_Full'].nunique()
    st.metric("Active States", total_states)
with col2:
    total_projects = len(filtered_df)
    st.metric("Total Projects", f"{total_projects:,}")
with col3:
    estimated_budget = filtered_df['Quantity_Procured'].sum() * 0.002
    st.metric("Total Budget", f"₹{estimated_budget:.0f} Cr")
with col4:
    if 'GST_Rate' in filtered_df.columns and not filtered_df.empty:
        avg_gst = filtered_df['GST_Rate'].mean()
        st.metric("Avg GST Rate", f"{avg_gst:.1f}%")
    else:
        st.metric("Avg GST Rate", "N/A")
st.markdown("---")

# ===== BUDGET UTILIZATION PROGRESS BAR =====
planned_budget = 4000  # Set as per organization policy
budget_utilized_pct = int((estimated_budget / planned_budget) * 100) if planned_budget > 0 else 0
if budget_utilized_pct > 100:
    budget_utilized_pct = 100
st.markdown("#### 💰 Budget Utilization")
st.progress(budget_utilized_pct, text=f"{budget_utilized_pct}% of planned budget used ({estimated_budget:.0f} Cr / {planned_budget} Cr)")
st.caption("Tracks actual procurement spend vs. your planning target. Update 'planned_budget' as needed.")

st.markdown("---")

# ========== MONTHLY TREND ==========
st.markdown("### 📈 Demand Trend Analysis")
if not filtered_df.empty:
    filtered_df['Month'] = filtered_df['Date'].dt.to_period('M').astype(str)
    monthly_demand = filtered_df.groupby('Month')['Quantity_Procured'].sum().reset_index()
    fig = px.line(
        monthly_demand,
        x='Month',
        y='Quantity_Procured',
        title='Monthly Material Demand Trend',
        labels={'Quantity_Procured': 'Total Quantity', 'Month': 'Month'},
        markers=True
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for selected filters.")

st.markdown("---")
st.caption("Data-driven procurement intelligence powered by AI analytics")
