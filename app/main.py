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
    
    # Let the user choose between straight lines and curves
    draw_mode_ui = st.radio(
        "Drawing Tool", 
        ["📏 Polygon (Straight Lines)", "✏️ Freedraw (Curved Corners)"]
    )
    canvas_mode = "polygon" if "Polygon" in draw_mode_ui else "freedraw"
    
    st.markdown("---")
    st.info("Set the local municipal bylaws.")
    uniform_setback = st.number_input("Uniform Setback (m)", min_value=0.5, value=1.5, step=0.5)
    
    st.markdown("---")
    st.subheader("Grid Optimization")
    max_span = st.slider("Max Column Span (m)", 3.0, 6.0, 4.5)

with col_draw:
    st.header("2. Draw Plot Boundary")
    if canvas_mode == "polygon":
        st.caption("Click to place corners. Double-click to close the shape. (Scale: 1px = 0.1m)")
    else:
        st.caption("Click and drag to draw custom curves. Make sure to close the loop! (Scale: 1px = 0.1m)")
    
    # The Interactive Canvas (Now supports dynamically changing modes)
    canvas_result = st_canvas(
        fill_color="rgba(46, 204, 113, 0.3)",  
        stroke_width=3,
        stroke_color="#27ae60",
        background_color="#f1f2f6",
        height=400,
        width=600,
        drawing_mode=canvas_mode,
        key="plot_canvas",
    )

# ==========================================
# PHASE 3: GEOMETRY ENGINE & AI GENERATION
# ==========================================
st.markdown("---")
st.header("3. AI Plan Generation")

if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
    objects = canvas_result.json_data["objects"]
    
    if len(objects) > 0:
        # Get the path data of the drawn shape
        # If freedraw is used, multiple objects might exist. We merge them or take the largest/last closed loop.
        # For simplicity, we'll take the most recently drawn object.
        path = objects[-1]["path"]
        raw_points = []
        
        # SMARTER SVG PARSER: Can now read Lines (L), Moves (M), and Bezier Curves (Q, C)
        for cmd in path:
            if cmd[0] in ['Z', 'z']: # Z means close path, no coordinates attached
                continue
            if len(cmd) >= 3:
                # In SVG paths, the last two numbers of any command are the final X, Y coordinates
                x, y = cmd[-2], cmd[-1]
                raw_points.append((x, y))
                
        if len(raw_points) >= 3:
            # 1. Scale pixels to real-world meters
            scale = 0.1
            real_points = [(x * scale, (400 - y) * scale) for x, y in raw_points] 
            
            # 2. Create the Plot Polygon using Shapely
            plot_poly = Polygon(real_points)
            
            # If the user drew a messy freedraw line that crosses itself, simplify it
            if not plot_poly.is_valid:
                plot_poly = plot_poly.buffer(0) 
            
            # 3. Calculate Buildable Envelope by shrinking the polygon
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
                minx, miny, maxx, maxy = buildable_poly.bounds
                
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
                        
                        # AI Check: Is this column legally inside the setback line?
                        if buildable_poly.contains(pt) or buildable_poly.exterior.distance(pt) < 0.1:
                            ai_columns_x.append(pt_x)
                            ai_columns_y.append(pt_y)
                
                # 5. Visualize the AI output
                with col_viz:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    
                    # Plot Property Line (Red)
                    if plot_poly.geom_type == 'Polygon':
                        x_plot, y_plot = plot_poly.exterior.xy
                        ax.plot(x_plot, y_plot, color='red', linewidth=2, label="Property Line")
                    
                    # Plot Buildable Line (Blue Dashed)
                    if buildable_poly.geom_type == 'Polygon':
                        x_build, y_build = buildable_poly.exterior.xy
                        ax.plot(x_build, y_build, color='blue', linestyle='--', linewidth=2, label="Setback Line")
                    
                    # Plot AI Columns
                    if ai_columns_x:
                        ax.scatter(ai_columns_x, ai_columns_y, color='black', marker='s', s=80, label="RCC Columns", zorder=5)
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
                        st.info(f"📐 AI successfully placed **{len(ai_columns_x)} columns** inside your curved geometry.")

    else:
        st.warning("Please draw a closed shape on the canvas above.")
