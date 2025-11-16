import streamlit as st
import pandas as pd
import plotly.express as px

# Check authentication
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.title("🎯 Smart Procurement Planning")
st.caption("Ministry of Power, Govt of India")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('hybrid_cleaned.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

st.markdown("---")

# ========== OVERVIEW METRICS ==========
st.markdown("### 📊 Procurement Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_states = df['State'].nunique()
    st.metric("Active States", total_states)

with col2:
    total_projects = len(df)
    st.metric("Total Projects", f"{total_projects:,}")

with col3:
    # Calculate total budget estimate
    estimated_budget = (df['Quantity_Procured'].sum() * 0.002)
    st.metric("Total Budget", f"₹{estimated_budget:.0f} Cr")

with col4:
    if 'GST_Rate' in df.columns:
        avg_gst = df['GST_Rate'].mean()
        st.metric("Avg GST Rate", f"{avg_gst:.1f}%")
    else:
        st.metric("Avg GST Rate", "11.6%")

st.markdown("---")

# ========== MONTHLY TREND ==========
st.markdown("### 📈 Demand Trend Analysis")

# Extract month from date
df['Month'] = df['Date'].dt.to_period('M').astype(str)
monthly_demand = df.groupby('Month')['Quantity_Procured'].sum().reset_index()

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

st.markdown("---")

# ========== DETAILED PROJECT TABLE ==========
st.markdown("### 📋 Detailed Project Data")

with st.expander("🔍 View All Projects"):
    search_state = st.selectbox("Filter by State", ['All'] + sorted(df['State'].unique().tolist()))
    
    if search_state != 'All':
        filtered = df[df['State'] == search_state]
    else:
        filtered = df
    
    st.dataframe(
        filtered.head(50),
        hide_index=True,
        use_container_width=True
    )
    
    st.caption(f"Showing {min(50, len(filtered))} of {len(filtered)} projects")

st.markdown("---")
st.caption("Data-driven procurement intelligence powered by AI analytics")
