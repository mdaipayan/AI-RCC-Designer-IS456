import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point

st.set_page_config(page_title="AI Architecture & RCC Designer", layout="wide")

st.title("🏗️ AI Plot Definition & Plan Generator (mm)")
st.markdown("Define your plot boundary using **Survey Coordinates (X, Y)**, set your rules, and let the AI generate the structural grid.")

# ==========================================
# PHASE 1 & 2: CONSTRAINTS & COORDINATES
# ==========================================
col_input, col_rules = st.columns([1, 1])

with col_rules:
    st.header("1. Environment & Rules")
    
    st.subheader("Municipal Bylaws")
    # Setbacks in mm
    uniform_setback = st.number_input("Uniform Setback (mm)", min_value=0, value=1500, step=100)
    
    st.markdown("---")
    st.subheader("Grid Optimization")
    # Spans in mm
    max_span = st.slider("Max Column Span (mm)", 3000, 6000, 4500, step=100)

with col_input:
    st.header("2. Plot Coordinates (mm)")
    st.caption("Enter the X and Y coordinates of the plot corners sequentially. You can add or delete rows.")
    
    # Default plot: A standard 12m x 18m rectangular plot (in mm)
    default_coords = pd.DataFrame({
        "X (mm)": [0, 12000, 12000, 0],
        "Y (mm)": [0, 0, 18000, 18000]
    })
    
    # st.data_editor allows the user to interactively edit the dataframe
    edited_df = st.data_editor(
        default_coords, 
        num_rows="dynamic", # Allows adding/deleting corners (e.g., for L-shapes or pentagons)
        use_container_width=True
    )

# ==========================================
# PHASE 3: GEOMETRY ENGINE & AI GENERATION
# ==========================================
st.markdown("---")
st.header("3. AI Plan Generation")

# Extract points from the table
raw_points = list(zip(edited_df["X (mm)"], edited_df["Y (mm)"]))

if len(raw_points) < 3:
    st.error("A plot must have at least 3 coordinate points to form a closed shape.")
else:
    # 1. Create the Plot Polygon using Shapely
    plot_poly = Polygon(raw_points)
    
    # Fix self-intersecting polygons (if the user enters coordinates out of order)
    if not plot_poly.is_valid:
        plot_poly = plot_poly.buffer(0) 
    
    if plot_poly.area == 0:
        st.error("Invalid coordinates. The calculated area is zero.")
    else:
        # 2. Calculate Buildable Envelope (shrink by setback in mm)
        buildable_poly = plot_poly.buffer(-uniform_setback)
        
        col_stats, col_viz = st.columns([1, 2])
        
        with col_stats:
            st.metric("Total Plot Area", f"{plot_poly.area / 1_000_000:.2f} sq.m")
            if buildable_poly.is_empty:
                st.error("Setbacks are too large! The buildable area has vanished.")
            else:
                st.metric("Buildable Area", f"{buildable_poly.area / 1_000_000:.2f} sq.m")
                st.success("Valid buildable envelope generated!")
        
        # 3. AI GRID GENERATION
        if not buildable_poly.is_empty:
            minx, miny, maxx, maxy = buildable_poly.bounds
            
            # Calculate grid divisions
            nx = int(np.ceil((maxx - minx) / max_span))
            ny = int(np.ceil((maxy - miny) / max_span))
            
            spacing_x = (maxx - minx) / nx if nx > 0 else max_span
            spacing_y = (maxy - miny) / ny if ny > 0 else max_span
            
            ai_columns_x, ai_columns_y = [], []
            
            for i in range(nx + 1):
                for j in range(ny + 1):
                    pt_x = minx + (i * spacing_x)
                    pt_y = miny + (j * spacing_y)
                    pt = Point(pt_x, pt_y)
                    
                    # Tolerance of 10mm to avoid dropping columns right on the edge due to floating point math
                    if buildable_poly.contains(pt) or buildable_poly.exterior.distance(pt) < 10.0:
                        ai_columns_x.append(pt_x)
                        ai_columns_y.append(pt_y)
            
            # 4. PROFESSIONAL VISUALIZATION WITH DIMENSIONS
            with col_viz:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Plot Polygons
                if plot_poly.geom_type == 'Polygon':
                    x_plot, y_plot = plot_poly.exterior.xy
                    ax.plot(x_plot, y_plot, color='red', linewidth=2, label="Property Line")
                
                if buildable_poly.geom_type == 'Polygon':
                    x_build, y_build = buildable_poly.exterior.xy
                    ax.plot(x_build, y_build, color='blue', linestyle='--', linewidth=2, label="Setback Line")
                
                # Plot AI Columns
                if ai_columns_x:
                    ax.scatter(ai_columns_x, ai_columns_y, color='black', marker='s', s=100, label="RCC Columns", zorder=5)
                    for x in set(ai_columns_x):
                        ax.axvline(x=x, color='gray', linestyle=':', alpha=0.4)
                    for y in set(ai_columns_y):
                        ax.axhline(y=y, color='gray', linestyle=':', alpha=0.4)
                        
                # --- ADDING DIMENSIONS TO THE DRAWING ---
                # Overall Width Annotation (X-axis max width)
                total_width = maxx - minx
                ax.annotate(
                    f"{total_width:.0f} mm",
                    xy=(minx, maxy + uniform_setback * 0.5),
                    xytext=(maxx, maxy + uniform_setback * 0.5),
                    arrowprops=dict(arrowstyle="<->", color="black"),
                    ha='center', va='bottom', fontsize=10, weight='bold'
                )
                ax.text((minx + maxx)/2, maxy + uniform_setback * 0.8, f"{total_width:.0f} mm Width", 
                        ha='center', va='bottom', fontsize=10, weight='bold', color='red')

                # Overall Depth Annotation (Y-axis max depth)
                total_depth = maxy - miny
                ax.annotate(
                    f"{total_depth:.0f} mm",
                    xy=(maxx + uniform_setback * 0.5, miny),
                    xytext=(maxx + uniform_setback * 0.5, maxy),
                    arrowprops=dict(arrowstyle="<->", color="black"),
                    ha='left', va='center', fontsize=10, weight='bold'
                )

                ax.set_aspect('equal')
                ax.set_title("AI Generated Structural Layout (Coordinates in mm)")
                ax.set_xlabel("X Coordinate (mm)")
                ax.set_ylabel("Y Coordinate (mm)")
                ax.legend(loc='upper right')
                
                # Show grid to reinforce the coordinate system
                ax.grid(True, linestyle='--', alpha=0.3)
                
                st.pyplot(fig)
                
                if ai_columns_x:
                    st.info(f"📐 AI successfully placed **{len(ai_columns_x)} columns**.\n\nAverage Grid Spacing: **{spacing_x:.0f} mm x {spacing_y:.0f} mm**.")
