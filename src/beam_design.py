import math

class BeamDesigner:
    """Designs Singly Reinforced RCC Beams per IS 456:2000."""
    
    def __init__(self, fck=25, fy=500):
        self.fck = fck
        self.fy = fy
        self.beams = {}

    def design_simply_supported_beam(self, beam_id, span_m, load_kN_m, b_mm=230):
        """
        Designs a beam for flexure and basic shear.
        load_kN_m should be the factored load (1.5 * (DL + LL))
        """
        L = span_m
        
        # 1. Calculate Max Bending Moment and Shear Force
        Mu_kNm = (load_kN_m * L**2) / 8
        Vu_kN = (load_kN_m * L) / 2
        
        Mu_Nmm = Mu_kNm * 1e6
        Vu_N = Vu_kN * 1000
        
        # 2. Check Required Depth for Singly Reinforced Section (Fe500)
        # Mu_lim = 0.133 * fck * b * d^2
        d_req = math.sqrt(Mu_Nmm / (0.133 * self.fck * b_mm))
        
        # Let's provide a standard architectural depth (round up to nearest 50mm)
        d_provided = math.ceil(d_req / 50) * 50
        D_total = d_provided + 50 # Add 50mm effective cover
        
        if D_total < 300: # Minimum practical beam depth
            D_total = 300
            d_provided = 250
            
        # 3. Calculate Required Tension Steel (Ast)
        # Quadratic equation: a*Ast^2 - b*Ast + c = 0
        term_a = (0.87 * self.fy**2) / (b_mm * self.fck)
        term_b = 0.87 * self.fy * d_provided
        term_c = Mu_Nmm
        
        # Using the simplified IS 456 formula for Ast
        ast = (0.5 * self.fck / self.fy) * (1 - math.sqrt(1 - (4.6 * Mu_Nmm) / (self.fck * b_mm * d_provided**2))) * b_mm * d_provided
        
        # Min and Max steel checks (Cl 26.5.1.1)
        ast_min = (0.85 * b_mm * d_provided) / self.fy
        ast_max = 0.04 * b_mm * D_total
        ast_provided = max(ast, ast_min)
        
        if ast_provided > ast_max:
            return f"Error: {beam_id} requires too much steel. Need a doubly reinforced beam or deeper section."

        # 4. Basic Shear Check (Nominal Shear Stress)
        tau_v = Vu_N / (b_mm * d_provided)
        tau_c_max = 3.1 # N/mm2 for M25 (Table 20)
        
        if tau_v > tau_c_max:
            return f"Error: {beam_id} fails in shear (tau_v > tau_c_max). Redesign section."
            
        shear_msg = f"Nominal Shear Stress = {tau_v:.2f} N/mm2. Provide shear stirrups."

        # 5. Calculate Bar Details (Assuming 16mm main bars)
        area_16mm = (math.pi / 4) * (16**2)
        no_of_bars = math.ceil(ast_provided / area_16mm)

        self.beams[beam_id] = {
            "Span (m)": L,
            "Moment (kNm)": round(Mu_kNm, 2),
            "Size (mm)": f"{b_mm} x {D_total}",
            "Ast Provided (mm2)": round(ast_provided, 2),
            "Main Rebar": f"{no_of_bars} - 16mm dia",
            "Shear Check": shear_msg
        }
        return self.beams[beam_id]

# Test the Engine:
# beam_engine = BeamDesigner(fck=25, fy=500)
# print(beam_engine.design_simply_supported_beam("B1", span_m=4.5, load_kN_m=35.0))
