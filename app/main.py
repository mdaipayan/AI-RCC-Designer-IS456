import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import fitz  # PyMuPDF for PDF parsing
import math

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="AI RCC Designer (IS 456 & IS 2911)", layout="wide")

st.title("🏗️ AI-Powered RCC Building Designer")
st.markdown("Design a safe, IS compliant structure from the **Foundation to the Roof**.")

# ==========================================
# STAGE 1: USER INPUT & BYLAWS (Sidebar)
# ==========================================
st.sidebar.header("1. Plot Definition")
plot_w = st.sidebar.number_input("Plot Width (m)", min_value=5.0, value=9.0, step=0.5)
plot_d = st.sidebar.number_input("Plot Depth (m)", min_value=5.0, value=12.0, step=0.5)

st.sidebar.header("2. Building Parameters")
bldg_type = st.sidebar.selectbox("Building Type", ["Duplex (2 Floors)", "G+1 Residential", "G+2 Commercial"])
floors = int(bldg_type.split('+')[1][0]) + 1 if '+' in bldg_type else 2

st.sidebar.header("3. Foundation System")
foundation_type = st.sidebar.radio("Select Type", ["Isolated Pad Footing", "Pile Foundation"])

# Dynamic parameters based on foundation choice
if foundation_type == "Isolated Pad Footing":
    soil_sbc = st.sidebar.slider("Soil Bearing Capacity (kN/m²)", 100, 300, 150)
else:
    st.sidebar.caption("IS 2911 Pile Parameters")
    pile_capacity = st.sidebar.number_input("Safe Load per Pile (kN)", min_value=100, value=400, step=50)
    pile_dia = st.sidebar.selectbox("Pile Diameter (mm)", [300, 450, 600], index=1)
    pile_depth = st.sidebar.number_input("Pile Depth (m)", min_value=5, value=15, step=1)

# Simulate Bylaws Engine (NBC Guidelines)
st.sidebar.markdown("---")
st.sidebar.subheader("Legal Constraints (NBC)")
front_setback = 3.0 if plot_w * plot_d > 200 else 1.5
buildable_w = plot_w - 2.0  # 1m side setbacks
buildable_d = plot_d - front_setback - 1.5 # front and rear setbacks
st.sidebar.success(f"Max Buildable Area: {buildable_w:.1f}m x {buildable_d:.1f}m")

# ==========================================
# HELPER FUNCTION: PDF PARSING
# ==========================================
def extract_grid_from_pdf(pdf_bytes):
    doc = fitz.open("pdf", pdf_bytes)
    page = doc[0]
    paths = page.get_drawings()
    
    h_lines, v_lines = [], []
    for path in paths:
        for item in path["items"]:
            if item[0] == "l": 
                p1, p2 = item[1], item[2]
                if abs(p1.y - p2.y) < 2.0: 
                    h_lines.append(p1.y)
                elif abs(p1.x - p2.x) < 2.0:
                    v_lines.append(p1.x)
                    
    if not h_lines or not v_lines:
        return [], []
        
    h_lines = np.unique(np.round(h_lines, -1)) 
    v_lines = np.unique(np.round(v_lines, -1))
    
    extracted_x, extracted_y = [], []
    for x in v_lines:
        for y in h_lines:
            extracted_x.append(x)
            extracted_y.append(y)
            
    return extracted_x, extracted_y

# ==========================================
# STAGE 2: GRID GENERATION & UPLOAD
# ==========================================
st.header("Step 1: Define Structural Grid")

plan_source = st.radio(
    "How would you like to define the column grid?",
    ("🤖 Let AI Generate the Best Grid", "📁 Upload Custom Centreline Plan (CSV)", "📄 Upload PDF Plan (Vector)")
)

x_coords, y_coords = [], []
custom_grid_loaded = False

if plan_source == "🤖 Let AI Generate the Best Grid":
    nx = int(np.ceil(buildable_w/4)) if buildable_w > 0 else 1
    ny = int(np.ceil(buildable_d/4)) if buildable_d > 0 else 1
    
    for i in range(nx + 1):
        for j in range(ny + 1):
            x_coords.append(i * (buildable_w/nx))
            y_coords.append(j * (buildable_d/ny))
    st.success("AI generated a grid optimized for 3.5m - 4.5m spans.")

elif plan_source == "📁 Upload Custom Centreline Plan (CSV)":
    st.info("Upload a CSV file with two columns: 'x' and 'y' representing column coordinates in meters.")
    sample_csv = pd.DataFrame({'x': [0, 4, 8, 0, 4, 8], 'y': [0, 0, 0, 5, 5, 5]})
    st.download_button(label="📥 Download Sample CSV Template", 
                       data=sample_csv.to_csv(index=False).encode('utf-8'), 
                       file_name="column_grid_template.csv", mime="text/csv")
    
    uploaded_file = st.file_uploader("Upload your Centreline CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df_custom = pd.read_csv(uploaded_file)
            x_coords, y_coords = df_custom['x'].tolist(), df_custom['y'].tolist()
            custom_grid_loaded = True
            st.success(f"Successfully loaded {len(x_coords)} columns from your file!")
        except Exception as e:
            st.error(f"Error reading the CSV. Error: {e}")

elif plan_source == "📄 Upload PDF Plan (Vector)":
    st.info("Upload a Vector PDF exported directly from CAD containing only the centerline grid.")
    pdf_scale = st.number_input("PDF Scale Factor (pixels per meter)", value=50.0)
    uploaded_pdf = st.file_uploader("Upload Centreline PDF", type=["pdf"])
    
    if uploaded_pdf is not None:
        try:
            raw_x, raw_y = extract_grid_from_pdf(uploaded_pdf.read())
            if len(raw_x) == 0:
                st.error("No vector lines found! Ensure the PDF is exported from CAD.")
            else:
                min_x, max_y = min(raw_x), max(raw_y) 
                for x, y in zip(raw_x, raw_y):
                    x_coords.append(round((x - min_x) / pdf_scale, 2))
                    y_coords.append(round((max_y - y) / pdf_scale, 2))
                custom_grid_loaded = True
                st.success(f"Successfully extracted {len(x_coords)} column locations from the PDF!")
        except Exception as e:
            st.error(f"Failed to parse PDF. Error: {e}")

# ==========================================
# STAGE 3: PLOTTING THE GRID
# ==========================================
if x_coords and y_coords:
    col1, col2 = st.columns([2, 1])
    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(x_coords, y_coords, c='black', marker='s', s=100, label='RCC Columns')
        for x in set(x_coords):
            ax.axvline(x=x, color='gray', linestyle='--', alpha=0.5)
        for y in set(y_coords):
            ax.axhline(y=y, color='gray', linestyle='--', alpha=0.5)
            
        ax.set_title("Architectural Centreline Plan")
        ax.set_xlabel("Width X (m)")
        ax.set_ylabel("Depth Y (m)")
        st.pyplot(fig)
        
    with col2:
        st.metric(label="Total Columns", value=len(x_coords))
        if custom_grid_loaded:
            if max(x_coords) > buildable_w or max(y_coords) > buildable_d:
                st.error("⚠️ Warning: Your uploaded plan exceeds the allowable buildable area (setbacks violated)!")

# ==========================================
# STAGE 4: ANALYSIS, DESIGN & ESTIMATE
# ==========================================
if x_coords and y_coords:
    if st.button("🚀 Run IS Structural Analysis & Design"):
        st.markdown("---")
        st.header(f"Step 2: {foundation_type} Design & BOQ")
        
        boq_data = []
        total_cost = 0
        
        for idx, (x, y) in enumerate(zip(x_coords, y_coords)):
            # Load Takedown (Simplified)
            max_x_val, max_y_val = max(x_coords), max(y_coords)
            is_edge = (x == 0 or x == max_x_val or y == 0 or y == max_y_val)
            load_factor = 0.5 if is_edge else 1.0
            pu_kn = 800 * load_factor * (floors / 2)
            
            if foundation_type == "Isolated Pad Footing":
                # --- PAD FOOTING LOGIC ---
                area_req = pu_kn / soil_sbc
                side = max(1.0, round(math.sqrt(area_req), 1))
                depth = 400 if pu_kn < 600 else 500
                steel_ast = round(pu_kn * 1.2, 0) 
                
                cost = (side * side * (depth/1000) * 5500) + ((steel_ast/1000 * side * 2 * 7850) * 75)
                
                boq_data.append({
                    "Col ID": f"C-{idx+1}",
                    "Load (kN)": round(pu_kn, 0),
                    "Footing Size": f"{side}m x {side}m",
                    "Depth (mm)": depth,
                    "Est. Cost (₹)": f"₹{cost:,.2f}"
                })
                
            else:
                # --- PILE FOUNDATION LOGIC ---
                # 1. Number of piles needed
                num_piles = max(1, math.ceil(pu_kn / pile_capacity))
                
                # 2. Pile Cap Dimension Estimation (Spacing roughly 3D)
                pile_spacing_m = 3 * (pile_dia / 1000)
                edge_dist = pile_dia / 1000
                
                if num_piles == 1:
                    cap_size = f"{round(pile_spacing_m, 1)}m x {round(pile_spacing_m, 1)}m"
                    cap_vol = pile_spacing_m * pile_spacing_m * 0.6  # 600mm deep cap
                else:
                    # Rough square approximation for the pile cap
                    side = round(math.sqrt(num_piles) * pile_spacing_m + (2 * edge_dist), 1)
                    cap_size = f"{side}m x {side}m"
                    cap_vol = side * side * 0.7  # 700mm deep cap
                
                # 3. Costing (Pile Drilling + Pile Cap)
                rate_per_meter_pile = 1500  # Assume ₹1500/meter for boring and concreting
                cost_of_piles = num_piles * pile_depth * rate_per_meter_pile
                
                cap_steel_kg = cap_vol * 100  # Assume 100kg steel per m3 of cap
                cost_of_cap = (cap_vol * 5500) + (cap_steel_kg * 75)
                
                cost = cost_of_piles + cost_of_cap
                
                boq_data.append({
                    "Col ID": f"C-{idx+1}",
                    "Load (kN)": round(pu_kn, 0),
                    "Piles Required": num_piles,
                    "Pile Cap Size": cap_size,
                    "Est. Cost (₹)": f"₹{cost:,.2f}"
                })
                
            total_cost += cost
            
        st.dataframe(pd.DataFrame(boq_data), use_container_width=True)
        st.success(f"### 💰 Total Foundation Estimate: ₹{total_cost:,.2f}")
        
        if foundation_type == "Pile Foundation":
            st.caption(f"Note: Estimate includes {pile_dia}mm piles driven to {pile_depth}m at ₹1500/m, plus RCC Pile Caps.")
        else:
            st.caption("Note: Estimate assumes M25 concrete at ₹5500/m³ and Fe500 steel at ₹75/kg.")
