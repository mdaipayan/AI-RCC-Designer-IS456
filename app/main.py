import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from streamlit_drawable_canvas import st_canvas
from shapely.geometry import Polygon, Point

st.set_page_config(page_title="AI Architecture & RCC Designer", layout="wide")

st.title("🏗️ AI Plot Definition & Plan Generator")
st.markdown("Draw your plot boundary, define the rules, and let the AI generate the structural grid.")

# ==========================================
# PHASE 1 & 2: CONSTRAINTS & DRAWING
# ==========================================
col_draw, col_rules = st.columns([2, 1])

with col_rules:
    st.header("1. Environment & Rules")
    st.info("Set the local municipal bylaws.")
    
    # Setbacks dictate how far from the property line we can build
    uniform_setback = st.number_input("Uniform Setback (m)", min_value=0.5, value=1.5, step=0.5)
    
    st.markdown("---")
    st.subheader("Grid Optimization")
    max_span = st.slider("Max Column Span (m)", 3.0, 6.0, 4.5)

with col_draw:
    st.header("2. Draw Plot Boundary")
    st.caption("Click to place corners. Double-click to close the polygon shape. (Grid scale: 1 pixel = 0.1m)")
    
    # The Interactive Canvas
    canvas_result = st_canvas(
        fill_color="rgba(46, 204, 113, 0.3)",  # Light Green Fill
        stroke_width=2,
        stroke_color="#27ae60",
        background_color="#f1f2f6",
        height=400,
        width=600,
        drawing_mode="polygon",
        key="plot_canvas",
    )

# ==========================================
# PHASE 3: GEOMETRY ENGINE & AI GENERATION
# ==========================================
st.markdown("---")
st.header("3. AI Plan Generation")

# Extract the drawn shape from the canvas
if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
    objects = canvas_result.json_data["objects"]
    
    if len(objects) > 0:
        # Get the path data of the drawn polygon
        path = objects[-1]["path"]
        raw_points = []
        
        # Parse the SVG-style path data from the canvas
        for cmd in path:
            if cmd[0] in ['M', 'L']: # M = Move to (start), L = Line to (corner)
                raw_points.append((cmd[1], cmd[2]))
                
        if len(raw_points) >= 3:
            # 1. Scale pixels to real-world meters (e.g., 10px = 1m)
            scale = 0.1
            real_points = [(x * scale, (400 - y) * scale) for x, y in raw_points] # Invert Y-axis for standard math
            
            # 2. Create the Plot Polygon using Shapely
            plot_poly = Polygon(real_points)
            
            # 3. Calculate Buildable Envelope by shrinking the polygon (Negative Buffer)
            # The buffer() function mathematically offsets the boundary inward
            buildable_poly = plot_poly.buffer(-uniform_setback)
            
            col_stats, col_viz = st.columns([1, 2])
            
            with col_stats:
                st.metric("Total Plot Area", f"{plot_poly.area:.1f} sqm")
                if buildable_poly.is_empty:
                    st.error("Setbacks are too large! The buildable area has vanished.")
                else:
                    st.metric("Buildable Area", f"{buildable_poly.area:.1f} sqm")
                    st.success("Valid buildable envelope generated!")
            
            # 4. AI Grid Generation Logic
            if not buildable_poly.is_empty:
                # Find the bounding box of the buildable area
                minx, miny, maxx, maxy = buildable_poly.bounds
                
                # Calculate number of bays needed
                nx = int(np.ceil((maxx - minx) / max_span))
                ny = int(np.ceil((maxy - miny) / max_span))
                
                spacing_x = (maxx - minx) / nx if nx > 0 else max_span
                spacing_y = (maxy - miny) / ny if ny > 0 else max_span
                
                # Generate columns ONLY if they fall inside the buildable polygon
                ai_columns_x, ai_columns_y = [], []
                
                for i in range(nx + 1):
                    for j in range(ny + 1):
                        pt_x = minx + (i * spacing_x)
                        pt_y = miny + (j * spacing_y)
                        pt = Point(pt_x, pt_y)
                        
                        # AI Check: Is this column legally inside the setback line?
                        if buildable_poly.contains(pt) or buildable_poly.exterior.distance(pt) < 0.1:
                            ai_columns_x.append(pt_x)
                            ai_columns_y.append(pt_y)
                
                # 5. Visualize the AI output
                with col_viz:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    
                    # Plot the Property Line (Red)
                    x_plot, y_plot = plot_poly.exterior.xy
                    ax.plot(x_plot, y_plot, color='red', linewidth=2, label="Property Line")
                    
                    # Plot the Setback / Buildable Line (Blue Dashed)
                    x_build, y_build = buildable_poly.exterior.xy
                    ax.plot(x_build, y_build, color='blue', linestyle='--', linewidth=2, label="Setback Line")
                    
                    # Plot the AI Columns (Black Squares)
                    if ai_columns_x:
                        ax.scatter(ai_columns_x, ai_columns_y, color='black', marker='s', s=80, label="RCC Columns", zorder=5)
                        
                        # Draw structural grid lines connecting the columns
                        for x in set(ai_columns_x):
                            ax.axvline(x=x, color='gray', linestyle=':', alpha=0.4)
                        for y in set(ai_columns_y):
                            ax.axhline(y=y, color='gray', linestyle=':', alpha=0.4)
                            
                    ax.set_aspect('equal')
                    ax.set_title("AI Generated Structural Layout")
                    ax.set_xlabel("Meters (X)")
                    ax.set_ylabel("Meters (Y)")
                    ax.legend()
                    st.pyplot(fig)
                    
                    if ai_columns_x:
                        st.info(f"📐 AI successfully placed **{len(ai_columns_x)} columns** with an average span of {spacing_x:.1f}m x {spacing_y:.1f}m inside your custom shape.")

    else:
        st.warning("Please draw a closed shape on the canvas above.")
