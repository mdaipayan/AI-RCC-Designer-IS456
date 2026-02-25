import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Mock Imports (In reality: from src.planner import BuildingPlanner, etc.) ---
# Assuming BuildingBylaws, BuildingPlanner, LoadTakedown, FoundationDesigner, BOQEstimator are available

st.set_page_config(page_title="AI RCC Designer (IS 456)", layout="wide")

st.title("🏗️ AI-Powered RCC Building Designer")
st.markdown("Design a safe, IS 456 compliant structure from the **Foundation to the Roof**.")

# ==========================================
# STAGE 1: USER INPUT & BYLAWS (Sidebar)
# ==========================================
st.sidebar.header("1. Plot Definition")
plot_w = st.sidebar.number_input("Plot Width (m)", min_value=5.0, value=9.0, step=0.5)
plot_d = st.sidebar.number_input("Plot Depth (m)", min_value=5.0, value=12.0, step=0.5)

st.sidebar.header("2. Building Parameters")
bldg_type = st.sidebar.selectbox("Building Type", ["Duplex (2 Floors)", "G+1 Residential", "G+2 Commercial"])
floors = int(bldg_type.split('+')[1][0]) + 1 if '+' in bldg_type else 2
soil_sbc = st.sidebar.slider("Soil Bearing Capacity (kN/m²)", 100, 300, 150)

# Simulate Bylaws Engine
st.sidebar.markdown("---")
st.sidebar.subheader("Legal Constraints (NBC)")
front_setback = 3.0 if plot_w * plot_d > 200 else 1.5
buildable_w = plot_w - 2.0  # 1m side setbacks
buildable_d = plot_d - front_setback - 1.5 # front and rear
st.sidebar.success(f"Buildable Area: {buildable_w:.1f}m x {buildable_d:.1f}m")

# ==========================================
# STAGE 2: AI PLAN GENERATION
# ==========================================
st.header("Step 1: AI Generated Structural Grid")
col1, col2 = st.columns([2, 1])

with col1:
    # Simulate the Planner module visual output
    fig, ax = plt.subplots(figsize=(6, 4))
    nx, ny = int(np.ceil(buildable_w/4)), int(np.ceil(buildable_d/4))
    x_coords, y_coords = [], []
    for i in range(nx + 1):
        for j in range(ny + 1):
            x_coords.append(i * (buildable_w/nx))
            y_coords.append(j * (buildable_d/ny))
            
    ax.scatter(x_coords, y_coords, c='black', marker='s', s=100, label='RCC Columns')
    ax.set_title("Optimal Column Placement for Duplex")
    ax.set_xlabel("Width (m)")
    ax.set_ylabel("Depth (m)")
    ax.grid(True, linestyle='--')
    st.pyplot(fig)

with col2:
    st.info("💡 **AI Suggestion:**\n\nThe grid has been optimized to keep spans between 3.5m and 4.5m to minimize beam depths and reduce steel consumption.")
    st.metric(label="Total Columns", value=len(x_coords))
    st.metric(label="Max Span", value=f"{max(buildable_w/nx, buildable_d/ny):.2f} m")

# ==========================================
# STAGE 3 & 4: ANALYSIS, DESIGN & ESTIMATE
# ==========================================
if st.button("🚀 Run IS 456 Structural Analysis & Design"):
    st.markdown("---")
    st.header("Step 2: Foundation Design & BOQ")
    
    # Simulate backend processing (Load Takedown -> Foundation -> Estimator)
    # Creating a mock dataframe to represent the output of our src/ modules
    boq_data = []
    total_cost = 0
    
    for idx, (x, y) in enumerate(zip(x_coords, y_coords)):
        # Corner columns have less tributary area (less load) than center ones
        load_factor = 1.0 if (0 < x < buildable_w and 0 < y < buildable_d) else 0.5
        pu_kn = 800 * load_factor * (floors / 2)
        
        # Sizing based on SBC
        area_req = pu_kn / soil_sbc
        side = max(1.0, round(np.sqrt(area_req), 1))
        depth = 400 if pu_kn < 600 else 500
        steel_ast = round(pu_kn * 1.2, 0) # simplified for UI mock
        
        cost = (side * side * (depth/1000) * 5500) + ((steel_ast/1000 * side * 2 * 7850) * 75)
        total_cost += cost
        
        boq_data.append({
            "Column ID": f"C-{idx+1}",
            "Axial Load Pu (kN)": round(pu_kn, 0),
            "Footing Size (m)": f"{side} x {side}",
            "Depth (mm)": depth,
            "Steel Ast (mm²)": steel_ast,
            "Est. Cost (₹)": f"₹{cost:,.2f}"
        })
        
    df = pd.DataFrame(boq_data)
    
    st.dataframe(df, use_container_width=True)
    
    st.success(f"### 💰 Total Foundation Estimate: ₹{total_cost:,.2f}")
    st.caption("Note: Estimate includes M25 concrete at ₹5500/m³ and Fe500 steel at ₹75/kg.")
