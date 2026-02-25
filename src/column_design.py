import math

class ColumnDesigner:
    """Designs RCC Columns per IS 456:2000."""
    
    def __init__(self, fck=25, fy=500):
        self.fck = fck
        self.fy = fy
        self.columns = {}

    def check_min_eccentricity(self, L_mm, D_mm):
        """Calculates minimum eccentricity (Cl 25.4)."""
        e_min = (L_mm / 500) + (D_mm / 30)
        return max(e_min, 20.0) # Must be at least 20mm

    def design_short_column(self, col_id, pu_kN, L_eff_m=3.0, b_mm=230, d_mm=400):
        """
        Designs longitudinal reinforcement for a short, axially loaded column.
        Assuming e_min <= 0.05 * D for this simplified educational module.
        """
        L_mm = L_eff_m * 1000
        Ag = b_mm * d_mm  # Gross Area
        
        # 1. Check Slenderness (Cl 25.1.2)
        slenderness = L_mm / min(b_mm, d_mm)
        if slenderness > 12:
            return f"Error: {col_id} is a Long Column (Ratio={slenderness:.1f}). Need P-Delta analysis."

        # 2. Check Eccentricity limit for simplified formula (Cl 39.3)
        e_min_x = self.check_min_eccentricity(L_mm, d_mm)
        if e_min_x > 0.05 * d_mm:
            # For educational purposes, we flag this. In reality, we'd use SP 16 Interaction Curves here.
            st_msg = "Needs Biaxial Bending Design (SP 16)"
        else:
            st_msg = "Axially Loaded Short Column"

        # 3. Calculate Required Steel Area (Asc)
        # Pu = 0.4 * fck * Ac + 0.67 * fy * Asc
        # Ac = Ag - Asc
        # Pu = 0.4 * fck * (Ag - Asc) + 0.67 * fy * Asc
        # Pu = 0.4*fck*Ag + Asc(0.67*fy - 0.4*fck)
        
        pu_N = pu_kN * 1000
        term1 = 0.4 * self.fck * Ag
        term2 = (0.67 * self.fy) - (0.4 * self.fck)
        
        asc_req = (pu_N - term1) / term2
        
        # 4. Enforce IS 456 limits (0.8% to 4%)
        min_steel = 0.008 * Ag
        max_steel = 0.04 * Ag
        
        asc_provided = max(asc_req, min_steel)
        
        if asc_provided > max_steel:
            return f"Error: {col_id} requires > 4% steel. Increase column size (b x d)!"

        # 5. Bar Sizing (Assuming 16mm bars standard for columns)
        area_16mm = (math.pi / 4) * (16**2)
        no_of_bars = math.ceil(asc_provided / area_16mm)
        no_of_bars = max(no_of_bars, 4) # Min 4 bars for rectangular column
        if no_of_bars % 2 != 0: 
            no_of_bars += 1 # Ensure symmetry (even number of bars)

        self.columns[col_id] = {
            "Size (mm)": f"{b_mm} x {d_mm}",
            "Status": st_msg,
            "Ast Required (mm2)": round(asc_provided, 2),
            "Steel %": round((asc_provided / Ag) * 100, 2),
            "Rebar Suggestion": f"{no_of_bars} - 16mm dia bars"
        }
        return self.columns[col_id]

# Test the Engine:
# col_engine = ColumnDesigner(fck=25, fy=500)
# print(col_engine.design_short_column("C-Central", pu_kN=1200))
