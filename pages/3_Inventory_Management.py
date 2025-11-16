import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import norm

# Check authentication
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.title("📦 Inventory Management")
st.caption("Ministry of Power, Govt of India")

# ==================== HELPER FUNCTIONS ====================

def calculate_inventory_metrics(avg_demand_per_day, lead_time_days, demand_std_dev, service_level=0.95):
    """Calculate safety stock and reorder point using Z-score method"""
    z_score = norm.ppf(service_level)
    safety_stock = z_score * demand_std_dev * np.sqrt(lead_time_days)
    reorder_point = (avg_demand_per_day * lead_time_days) + safety_stock
    
    return {
        'safety_stock': int(max(safety_stock, 0)),
        'reorder_point': int(max(reorder_point, 0)),
        'z_score': round(z_score, 2)
    }

def calculate_eoq(annual_demand, ordering_cost, unit_cost, holding_rate):
    """Calculate Economic Order Quantity"""
    holding_cost = unit_cost * (holding_rate / 100)
    eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
    return int(eoq)

# ==================== LOAD INVENTORY DATA ====================

@st.cache_data
def load_inventory():
    """Generate complete inventory data"""
    materials = ['Steel', 'Cement', 'Conductors', 'Equipment']
    data = []
    
    np.random.seed(42)
    
    for i, material in enumerate(materials):
        for j in range(5):
            avg_daily_demand = np.random.randint(20, 80)
            demand_std_dev = avg_daily_demand * 0.3
            lead_time_days = np.random.randint(15, 45)
            
            metrics = calculate_inventory_metrics(
                avg_daily_demand, 
                lead_time_days, 
                demand_std_dev
            )
            
            reorder_point = metrics['reorder_point']
            
            # Create low stock scenarios
            if material == 'Cement':
                if j == 0:
                    current_stock = int(reorder_point * 0.3)
                elif j == 1:
                    current_stock = int(reorder_point * 0.5)
                elif j == 2:
                    current_stock = int(reorder_point * 0.6)
                elif j == 3:
                    current_stock = int(reorder_point * 0.7)
                else:
                    current_stock = int(reorder_point * 0.65)
                    
            elif material == 'Equipment':
                if j == 0:
                    current_stock = int(reorder_point * 0.2)
                elif j == 1:
                    current_stock = int(reorder_point * 0.3)
                elif j == 2:
                    current_stock = int(reorder_point * 0.35)
                elif j == 3:
                    current_stock = int(reorder_point * 0.4)
                else:
                    current_stock = int(reorder_point * 0.25)
                    
            else:
                current_stock = np.random.randint(int(reorder_point * 1.2), int(reorder_point * 2.5))
            
            # Calculate status
            if current_stock < reorder_point * 0.5:
                status = 'Critical'
            elif current_stock < reorder_point:
                status = 'Low Stock'
            else:
                status = 'In Stock'
            
            data.append({
                'Material_ID': f'M{i}{j:03d}',
                'Material': material,
                'Current_Stock': current_stock,
                'Reorder_Point': reorder_point,
                'Safety_Stock': metrics['safety_stock'],
                'Avg_Daily_Demand': avg_daily_demand,
                'Lead_Time_Days': lead_time_days,
                'Unit_Cost': round(np.random.uniform(50, 500), 2),
                'Supplier': f'Supplier {chr(65 + np.random.randint(0, 5))}',
                'Status': status,
                'Service_Level': '95%'
            })
    
    return pd.DataFrame(data)

inventory_df = load_inventory()

st.markdown("---")

# ==================== SEARCH & FILTER ====================

st.markdown("### 🔍 Search & Filter Inventory")

col1, col2, col3 = st.columns(3)

with col1:
    search_term = st.text_input("🔎 Search Material ID", placeholder="Enter Material ID...")

with col2:
    material_filter = st.multiselect(
        "Material Type", 
        options=inventory_df['Material'].unique(),
        default=inventory_df['Material'].unique()
    )

with col3:
    status_filter = st.multiselect(
        "Status",
        options=['In Stock', 'Low Stock', 'Critical'],
        default=['In Stock', 'Low Stock', 'Critical']
    )

# Apply filters
filtered_df = inventory_df.copy()

if search_term:
    filtered_df = filtered_df[filtered_df['Material_ID'].str.contains(search_term, case=False)]

filtered_df = filtered_df[filtered_df['Material'].isin(material_filter)]
filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]

st.markdown(f"**Showing {len(filtered_df)} of {len(inventory_df)} items**")

st.markdown("---")

# ==================== DETAILED INVENTORY TABLE ====================

st.markdown("### 📋 Detailed Inventory View")

def get_status_icon(status):
    icons = {
        'In Stock': '🟢',
        'Low Stock': '🟠',
        'Critical': '🔴'
    }
    return icons.get(status, '⚪')

display_df = filtered_df.copy()
display_df[''] = display_df['Status'].apply(get_status_icon)

st.dataframe(
    display_df[['', 'Material_ID', 'Material', 'Current_Stock', 
                'Reorder_Point', 'Safety_Stock', 'Avg_Daily_Demand',
                'Unit_Cost', 'Supplier', 'Lead_Time_Days', 'Service_Level', 'Status']],
    column_config={
        "": st.column_config.TextColumn("", width="small"),
        "Material_ID": "ID",
        "Material": "Material",
        "Current_Stock": st.column_config.NumberColumn("Current Stock", format="%d units"),
        "Reorder_Point": st.column_config.NumberColumn("Reorder Point", format="%d units"),
        "Safety_Stock": st.column_config.NumberColumn("Safety Stock", format="%d units"),
        "Avg_Daily_Demand": st.column_config.NumberColumn("Avg Demand/Day", format="%d"),
        "Unit_Cost": st.column_config.NumberColumn("Unit Cost", format="₹%.2f"),
        "Supplier": "Supplier",
        "Lead_Time_Days": st.column_config.NumberColumn("Lead Time", format="%d days"),
        "Service_Level": "Service Level",
        "Status": st.column_config.TextColumn("Status", width="medium")
    },
    hide_index=True,
    use_container_width=True,
    height=400
)

st.caption("**Status Logic:** 🟢 Above reorder point | 🟠 Below reorder point | 🔴 Below 50% of reorder")

st.markdown("---")

# ==================== CRITICAL ALERTS ====================

st.markdown("### 🚨 Stock Alerts")

critical_items = filtered_df[filtered_df['Status'] == 'Critical']
if len(critical_items) > 0:
    st.error(f"**🔴 {len(critical_items)} CRITICAL items require IMMEDIATE procurement!**")
    for _, item in critical_items.head(5).iterrows():
        qty_needed = item['Reorder_Point'] - item['Current_Stock']
        est_cost = qty_needed * item['Unit_Cost']
        st.error(
            f"🔴 **{item['Material']}** (ID: {item['Material_ID']}) - "
            f"Stock: {item['Current_Stock']} units | Need: {qty_needed} units (₹{est_cost:,.0f})"
        )
else:
    st.success("✅ No critical items")

low_stock_items = filtered_df[filtered_df['Status'] == 'Low Stock']
if len(low_stock_items) > 0:
    with st.expander(f"🟠 View {len(low_stock_items)} Low Stock Items"):
        st.dataframe(
            low_stock_items[['Material_ID', 'Material', 'Current_Stock', 'Reorder_Point', 
                           'Safety_Stock', 'Supplier', 'Lead_Time_Days']], 
            hide_index=True, 
            use_container_width=True
        )

st.markdown("---")
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Export to CSV",
    data=csv,
    file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True,
    type="primary"
)

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
