import pandas as pd
import numpy as np
from scipy.stats import norm


def calculate_inventory_metrics(avg_demand_per_day, lead_time_days, demand_std_dev, service_level=0.95):
    """Calculate safety stock and reorder point using Z-score method"""
    try:
        z_score = norm.ppf(service_level)
        safety_stock = z_score * demand_std_dev * np.sqrt(lead_time_days)
        reorder_point = (avg_demand_per_day * lead_time_days) + safety_stock
        
        return {
            'safety_stock': int(max(safety_stock, 0)),
            'reorder_point': int(max(reorder_point, 0))
        }
    except Exception as e:
        print(f"Error in calculate_inventory_metrics: {e}")
        return {'safety_stock': 100, 'reorder_point': 500}


def load_full_inventory():
    """Generate complete inventory with all SKUs - creates matching sums for dashboard"""
    try:
        materials = ['Steel', 'Cement', 'Conductors', 'Equipment']
        data = []
        
        np.random.seed(42)  # Consistent data generation
        
        for i, material in enumerate(materials):
            for j in range(5):  # 5 SKUs per material
                avg_daily_demand = np.random.randint(20, 80)
                demand_std_dev = avg_daily_demand * 0.3
                lead_time_days = np.random.randint(15, 45)
                
                metrics = calculate_inventory_metrics(
                    avg_daily_demand, 
                    lead_time_days, 
                    demand_std_dev
                )
                
                reorder_point = metrics['reorder_point']
                
                # MAKE MULTIPLE SKUs LOW/CRITICAL SO SUM TRIGGERS ALERTS
                if material == 'Cement':
                    # Make ALL 5 cement SKUs low so their SUM is also low
                    if j == 0:
                        current_stock = int(reorder_point * 0.3)
                    elif j == 1:
                        current_stock = int(reorder_point * 0.5)
                    elif j == 2:
                        current_stock = int(reorder_point * 0.6)
                    elif j == 3:
                        current_stock = int(reorder_point * 0.7)
                    else:  # j == 4
                        current_stock = int(reorder_point * 0.65)
                        
                elif material == 'Equipment':
                    # Make ALL 5 equipment SKUs critical so their SUM is critical
                    if j == 0:
                        current_stock = int(reorder_point * 0.2)
                    elif j == 1:
                        current_stock = int(reorder_point * 0.3)
                    elif j == 2:
                        current_stock = int(reorder_point * 0.35)
                    elif j == 3:
                        current_stock = int(reorder_point * 0.4)
                    else:  # j == 4
                        current_stock = int(reorder_point * 0.25)
                        
                else:
                    # Steel and Conductors = In Stock (normal high values)
                    current_stock = np.random.randint(int(reorder_point * 1.2), int(reorder_point * 2.5))
                
                # Calculate status AFTER setting current_stock
                if current_stock < reorder_point * 0.5:
                    status = 'Critical'
                elif current_stock < reorder_point:
                    status = 'Low Stock'
                else:
                    status = 'In Stock'
                
                # Now append with status defined
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
        
        df = pd.DataFrame(data)
        print(f"✅ load_full_inventory generated {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"❌ Error in load_full_inventory: {e}")
        return pd.DataFrame(columns=['Material_ID', 'Material', 'Current_Stock', 'Reorder_Point', 
                                    'Safety_Stock', 'Avg_Daily_Demand', 'Lead_Time_Days', 
                                    'Unit_Cost', 'Supplier', 'Status', 'Service_Level'])


def get_dashboard_summary():
    """Get aggregated data for dashboard - TRUE SUM from all SKUs"""
    try:
        full_inventory = load_full_inventory()
        
        if full_inventory.empty:
            print("⚠️ Warning: full_inventory is empty")
            return pd.DataFrame(columns=['Material', 'Stock', 'Reorder_Point', 'Status'])
        
        # Sum all SKUs by material type
        summary = full_inventory.groupby('Material').agg({
            'Current_Stock': 'sum',
            'Reorder_Point': 'max'
        }).reset_index()
        
        # Rename to match dashboard column names
        summary.rename(columns={'Current_Stock': 'Stock'}, inplace=True)
        
        # Calculate status based on summed values
        def calc_status(stock, reorder):
            if stock >= reorder:
                return '🟢 In Stock'
            elif stock < reorder * 0.5:
                return '🔴 Critical'
            else:
                return '🟡 Low Stock'
        
        summary['Status'] = summary.apply(
            lambda row: calc_status(row['Stock'], row['Reorder_Point']),
            axis=1
        )
        
        print(f"✅ get_dashboard_summary generated {len(summary)} rows")
        return summary
        
    except Exception as e:
        print(f"❌ Error in get_dashboard_summary: {e}")
        return pd.DataFrame(columns=['Material', 'Stock', 'Reorder_Point', 'Status'])


# Test when run directly
if __name__ == "__main__":
    print("Testing inventory_data.py...")
    print("\n1. Testing load_full_inventory():")
    inv = load_full_inventory()
    print(inv.head())
    print(f"\nTotal rows: {len(inv)}")
    
    print("\n2. Testing get_dashboard_summary():")
    summary = get_dashboard_summary()
    print(summary)
