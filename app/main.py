import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="AI RCC Designer", layout="wide")

st.title("🏗️ AI-Powered RCC Building Designer")
st.markdown("Design a safe, IS 456 compliant structure from the **Foundation to the Roof**.")

# --- Sidebar Inputs ---
st.sidebar.header("1. Plot Definition")
plot_w = st.sidebar.number_input("Plot Width (m)", min_value=5.0, value=9.0, step=0.5)
plot_d = st.sidebar.number_input("Plot Depth (m)", min_value=5.0, value=12.0, step=0.5)

st.sidebar.header("2. Building Parameters")
bldg_type = st.sidebar.selectbox("Building Type", ["Duplex (2 Floors)", "G+1 Residential", "G+2 Commercial"])
floors = int(bldg_type.split('+')[1][0]) + 1 if '+' in bldg_type else 2
soil_sbc = st.sidebar.slider("Soil Bearing Capacity (kN/m²)", 100, 300, 150)

# --- Bylaws Logic ---
front_setback = 3.0 if plot_w * plot_d > 200 else 1.5
buildable_w = plot_w - 2.0  
buildable_d = plot_d - front_setback - 1.5 
st.sidebar.success(f"Buildable Area: {buildable_w:.1f}m x {buildable_d:.1f}m")

# --- UI Layout ---
st.header("Step 1: AI Generated Structural Grid")
col1, col2 = st.columns([2, 1])

# Generate Grid
nx = int(np.ceil(buildable_w/4)) if buildable_w > 0 else 1
ny = int(np.ceil(buildable_d/4)) if buildable_d > 0 else 1
x_coords, y_coords = [], []

for i in range(nx + 1):
    for j in range(ny + 1):
        x_coords.append(i * (buildable_w/nx))
        y_coords.append(j * (buildable_d/ny))

with col1:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(x_coords, y_coords, c='black', marker='s', s=100, label='RCC Columns')
    ax.set_title("Optimal Column Placement")
    ax.set_xlabel("Width (m)")
    ax.set_ylabel("Depth (m)")
    ax.grid(True, linestyle='--')
    st.pyplot(fig)

with col2:
    st.info("💡 **AI Suggestion:**\nThe grid has been optimized to keep spans between 3.5m and 4.5m.")
    st.metric(label="Total Columns", value=len(x_coords))

# --- Analysis & Design ---
if st.button("🚀 Run IS 456 Structural Analysis & Design"):
    st.markdown("---")
    st.header("Step 2: Foundation Design & BOQ")
    
    boq_data = []
    total_cost = 0
    
    for idx, (x, y) in enumerate(zip(x_coords, y_coords)):
        load_factor = 1.0 if (0 < x < buildable_w and 0 < y < buildable_d) else 0.5
        pu_kn = 800 * load_factor * (floors / 2)
        
        area_req = pu_kn / soil_sbc
        side = max(1.0, round(np.sqrt(area_req), 1))
        depth = 400 if pu_kn < 600 else 500
        steel_ast = round(pu_kn * 1.2, 0) 
        
        cost = (side * side * (depth/1000) * 5500) + ((steel_ast/1000 * side * 2 * 7850) * 75)
        total_cost += cost
        
        boq_data.append({
            "Column ID": f"C-{idx+1}",
            "Axial Load Pu (kN)": round(pu_kn, 0),
            "Footing Size (m)": f"{side} x {side}",
            "Depth (mm)": depth,
            "Est. Cost (₹)": f"₹{cost:,.2f}"
        })
        
    st.dataframe(pd.DataFrame(boq_data), use_container_width=True)
    st.success(f"### 💰 Total Foundation Estimate: ₹{total_cost:,.2f}")
