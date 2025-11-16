import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="POWERGRID Forecasting",
    page_icon="🔌",
    layout="wide"
)

# ========== HIDE DEFAULT NAVIGATION ==========
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ========== AUTHENTICATION ==========

def initialize_session_state():
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = False
    if 'name' not in st.session_state:
        st.session_state['name'] = None

def check_credentials(username, password):
    users = {
        'admin': {'password': 'admin123', 'name': 'Admin'},
        'powergrid': {'password': 'sih2025', 'name': 'POWERGRID'}
    }
    if username in users and users[username]['password'] == password:
        return True, users[username]['name']
    return False, None

def logout():
    st.session_state['authentication_status'] = False
    st.session_state['name'] = None
    st.rerun()

initialize_session_state()

# ========== SIDEBAR ==========

with st.sidebar:
    st.markdown("### 🔌 POWERGRID")
    st.markdown("**Supply Chain AI**")
    st.markdown("---")
    
    if st.session_state['authentication_status']:
        st.success(f"✅ {st.session_state['name']}")
        
        if st.button("Logout", use_container_width=True):
            logout()
        
        st.markdown("---")
        
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
        
        if st.button("🔮 Forecast", use_container_width=True):
            st.switch_page("pages/2_Demand_Forecast.py")
        
        if st.button("📦 Inventory", use_container_width=True):
            st.switch_page("pages/3_Inventory_Management.py")
        
        if st.button("🎯 Procurement", use_container_width=True):
            st.switch_page("pages/4_Procurement_Planning.py")
        
    else:
        st.markdown("### Login")
        
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", use_container_width=True):
                valid, name = check_credentials(u, p)
                if valid:
                    st.session_state['authentication_status'] = True
                    st.session_state['name'] = name
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.info("**Demo:**\n\n`admin` / `admin123`")

# ========== LOAD INVENTORY DATA ==========

from inventory_data import get_dashboard_summary

@st.cache_data
def load_dashboard_data():
    """Load dashboard summary (aggregated from all SKUs)"""
    return get_dashboard_summary()

def calculate_status(stock, reorder):
    if stock >= reorder:
        return '🟢 In Stock'
    elif stock < reorder * 0.5:
        return '🔴 Critical'
    else:
        return '🟡 Low Stock'

# ========== DIALOG BOX ==========

@st.dialog("🚨 Critical Stock Alert")
def show_critical_alert(critical_items_df):
    st.error("**Immediate Attention Required!**")
    st.write(f"**{len(critical_items_df)} material(s) below reorder threshold**")
    
    st.markdown("---")
    
    for idx, item in critical_items_df.iterrows():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if item['Stock'] < item['Reorder_Point'] * 0.5:
                st.error(f"🔴 **{item['Material']}** - CRITICAL")
                level = "CRITICAL"
            else:
                st.warning(f"🟡 **{item['Material']}** - Low Stock")
                level = "LOW"
            
            st.write(f"Current: **{item['Stock']} units**")
            st.write(f"Reorder at: **{item['Reorder_Point']} units**")
            shortage = item['Reorder_Point'] - item['Stock']
            st.write(f"Shortage: **{shortage} units**")
            percentage = (item['Stock'] / item['Reorder_Point']) * 100
            st.write(f"Stock Level: **{percentage:.1f}%** of reorder point")
        
        with col2:
            st.metric("Level", level, delta=f"-{shortage}")
        
        st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Go to Inventory", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Inventory_Management.py")
    with col2:
        if st.button("❌ Dismiss", use_container_width=True):
            st.session_state['alert_dismissed'] = True
            st.rerun()

# ========== MAIN CONTENT ==========

if st.session_state['authentication_status']:
    
    st.title("🔌 POWERGRID Material Forecasting")
    st.caption("Ministry of Power, Govt of India")
    st.markdown("---")
    
    # ========== LOAD INVENTORY DATA ==========
    
    materials_data = load_dashboard_data()
    
    # MATERIAL INVENTORY
    st.markdown("### 📦 Material Inventory Status")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.dataframe(
            materials_data,
            column_config={
                'Material': st.column_config.TextColumn("Material", width="medium"),
                'Stock': st.column_config.NumberColumn("Stock", format="%d units"),
                'Reorder_Point': st.column_config.NumberColumn("Reorder", format="%d"),
                'Status': st.column_config.TextColumn("Status", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )
    
    with col2:
        fig = px.pie(
            materials_data, 
            values='Stock',
            names='Material',
            hole=0.4,
            color_discrete_sequence=['#00D9FF', '#FFA500', '#00FF88', '#FF4444']
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{value} units<br>%{percent}<extra></extra>'
        )
        fig.update_layout(height=280, showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
        
        st.plotly_chart(fig, use_container_width=True, key="home_pie")
    
    st.caption("**Status Logic:** 🟢 Above reorder | 🟡 Below reorder | 🔴 Below 50% of reorder")
    
    st.markdown("---")
    
    # ALERTS
    st.markdown("### 🔔 Smart Alerts")
    
    critical_items = materials_data[materials_data['Stock'] < materials_data['Reorder_Point']]
    
    if len(critical_items) > 0:
        for idx, item in critical_items.iterrows():
            shortage = item['Reorder_Point'] - item['Stock']
            percentage = (item['Stock'] / item['Reorder_Point']) * 100
            
            if item['Stock'] < item['Reorder_Point'] * 0.5:
                st.error(
                    f"🔴 **CRITICAL: {item['Material']}** - Stock at {item['Stock']} units "
                    f"({percentage:.1f}% of reorder point) | Shortage: {shortage} units"
                )
            else:
                st.warning(
                    f"🟡 **LOW STOCK: {item['Material']}** - {item['Stock']} units "
                    f"({percentage:.1f}% of reorder point) | Need: {shortage} units"
                )
        
        st.markdown("")
        if st.button("🔍 View Detailed Alert", type="secondary", use_container_width=True):
            show_critical_alert(critical_items)
    else:
        st.success("✅ All materials adequately stocked")
    
    if 'forecast_df' in st.session_state:
        st.success("✅ Forecast available for viewing")
    
    st.markdown("---")
    
    # QUICK ACTIONS
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔮 Generate Forecast", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Demand_Forecast.py")
    
    with col2:
        if st.button("📦 Manage Inventory", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Inventory_Management.py")
    
    # AUTO DIALOG
    if 'dialog_shown' not in st.session_state:
        st.session_state['dialog_shown'] = False
    if 'alert_dismissed' not in st.session_state:
        st.session_state['alert_dismissed'] = False
    
    if not st.session_state['dialog_shown'] and not st.session_state['alert_dismissed']:
        if len(critical_items) > 0:
            st.toast("⚠️ Critical stock alert detected!", icon="🚨")
            show_critical_alert(critical_items)
            st.session_state['dialog_shown'] = True

else:
    
    # ========== WELCOME SCREEN ==========
    
    st.title("🔌 POWERGRID Material Forecasting")
    st.markdown("### AI-Powered Supply Chain Intelligence")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🔮 AI Forecasting**
        
        Prophet algorithm
        
        • 6-36 month predictions  
        • Confidence intervals  
        • High accuracy
        """)
    
    with col2:
        st.info("""
        **📦 Inventory Management**
        
        Real-time tracking
        
        • Smart alerts    
        • Status monitoring
        """)
    
    st.warning("👈 Login using sidebar")

st.markdown("---")
st.caption("© 2025 POWERGRID Corporation of India | Ministry of Power")
