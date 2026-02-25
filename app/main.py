import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from streamlit_drawable_canvas import st_canvas
from shapely.geometry import Polygon, Point

st.set_page_config(page_title="AI Architecture & RCC Designer", layout="wide")

st.title("🏗️ AI Plot Definition & Plan Generator (mm)")
st.markdown("Draw your plot boundary, define the actual length, and let the AI generate the structural grid in **millimeters**.")

# ==========================================
# PHASE 1 & 2: CONSTRAINTS & DRAWING
# ==========================================
col_draw, col_rules = st.columns([2, 1])

with col_rules:
    st.header("1. Environment & Rules")
    
    draw_mode_ui = st.radio("Drawing Tool", ["📏 Polygon (Straight Lines)", "✏️ Freedraw (Curved Corners)"])
    canvas_mode = "polygon" if "Polygon" in draw_mode_ui else "freedraw"
    
    st.markdown("---")
    st.subheader("Scale Calibration")
    st.info("Draw your shape, then tell the AI how wide it is in real life.")
    # The user enters the actual width of the plot they drew
    actual_width_mm = st.number_input("Actual Plot Width (mm)", min_value=1000, value=9000, step=500)
    
    st.markdown("---")
    st.subheader("Municipal Bylaws")
    # Setbacks now in mm
    uniform_setback = st.number_input("Uniform Setback (mm)", min_value=0, value=1500, step=100)
    
    st.markdown("---")
    st.subheader("Grid Optimization")
    # Spans now in mm
    max_span = st.slider("Max Column Span (mm)", 3000, 6000, 4500, step=100)

with col_draw:
    st.header("2. Draw Plot Boundary")
    st.caption("Proportionally sketch your plot shape here. Double-click to close.")
    
    # The Interactive Canvas
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
        path = objects[-1]["path"]
        raw_points = []
        
        for cmd in path:
            if cmd[0] in ['Z', 'z']: 
                continue
            if len(cmd) >= 3:
                x, y = cmd[-2], cmd[-1]
                raw_points.append((x, y))
                
        if len(raw_points) >= 3:
            # --- 1. SCALE CALIBRATION ---
            # Find how many pixels wide the user's drawing is
            pixel_xs = [pt[0] for pt in raw_points]
            pixel_width = max(pixel_xs) - min(pixel_xs)
            
            if pixel_width > 0:
                # Calculate scale: mm per pixel
                scale = actual_width_mm / pixel_width
                
                # Convert all raw pixel points to real-world mm points
                # (We also invert the Y-axis so standard Math applies)
                real_points = [(x * scale, (400 - y) * scale) for x, y in raw_points]
                
                # --- 2. SHAPELY GEOMETRY ---
                plot_poly = Polygon(real_points)
                if not plot_poly.is_valid:
                    plot_poly = plot_poly.buffer(0) 
                
                # Calculate Buildable Envelope (shrink by setback in mm)
                buildable_poly = plot_poly.buffer(-uniform_setback)
                
                col_stats, col_viz = st.columns([1, 2])
                
                with col_stats:
                    st.metric("Total Plot Area", f"{plot_poly.area / 1_000_000:.2f} sq.m")
                    if buildable_poly.is_empty:
                        st.error("Setbacks are too large! The buildable area has vanished.")
                    else:
                        st.metric("Buildable Area", f"{buildable_poly.area / 1_000_000:.2f} sq.m")
                        st.success("Valid buildable envelope generated!")
                
                # --- 3. AI GRID GENERATION ---
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
                            
                            # Tolerance of 10mm (0.01m) to avoid floating point dropouts
                            if buildable_poly.contains(pt) or buildable_poly.exterior.distance(pt) < 10.0:
                                ai_columns_x.append(pt_x)
                                ai_columns_y.append(pt_y)
                    
                    # --- 4. PROFESSIONAL VISUALIZATION WITH DIMENSIONS ---
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
                            # 230mm roughly represents standard column size visually
                            ax.scatter(ai_columns_x, ai_columns_y, color='black', marker='s', s=100, label="RCC Columns", zorder=5)
                            for x in set(ai_columns_x):
                                ax.axvline(x=x, color='gray', linestyle=':', alpha=0.4)
                            for y in set(ai_columns_y):
                                ax.axhline(y=y, color='gray', linestyle=':', alpha=0.4)
                                
                        # --- ADDING DIMENSIONS TO THE DRAWING ---
                        # Overall Width Annotation (Top)
                        ax.annotate(
                            f"{actual_width_mm:.0f} mm",
                            xy=(min(pixel_xs) * scale, maxy + uniform_setback * 0.5),
                            xytext=(max(pixel_xs) * scale, maxy + uniform_setback * 0.5),
                            arrowprops=dict(arrowstyle="<->", color="black"),
                            ha='center', va='bottom', fontsize=10, weight='bold'
                        )
                        # Put the text right in the middle of the arrow
                        ax.text(
                            ((min(pixel_xs) + max(pixel_xs))/2) * scale, 
                            maxy + uniform_setback * 0.8, 
                            f"{actual_width_mm:.0f} mm Width", 
                            ha='center', va='bottom', fontsize=10, weight='bold', color='red'
                        )

                        # Setback Dimension Annotation (Side)
                        ax.annotate(
                            f"SB: {uniform_setback} mm",
                            xy=(maxx, (miny+maxy)/2),
                            xytext=(maxx + uniform_setback, (miny+maxy)/2),
                            arrowprops=dict(arrowstyle="<->", color="blue"),
                            ha='left', va='center', fontsize=9, color='blue'
                        )

                        ax.set_aspect('equal')
                        ax.set_title("AI Generated Structural Layout (Dimensions in mm)")
                        ax.set_xlabel("X (mm)")
                        ax.set_ylabel("Y (mm)")
                        ax.legend(loc='upper right')
                        st.pyplot(fig)
                        
                        if ai_columns_x:
                            st.info(f"📐 AI successfully placed **{len(ai_columns_x)} columns**.\n\nAverage Grid Spacing: **{spacing_x:.0f} mm x {spacing_y:.0f} mm**.")

            else:
                st.error("Please draw a valid shape with width.")
    else:
        st.warning("Please draw a closed shape on the canvas above.")
