import math

class FoundationDesigner:
    def __init__(self, sbc=200, fck=25, fy=500):
        self.sbc = sbc      # Soil Bearing Capacity in kN/m2
        self.fck = fck      # Grade of Concrete (M25)
        self.fy = fy        # Grade of Steel (Fe500)
        self.footings = {}

    def design_isolated_footing(self, col_id, pu_kN, col_dim=0.300):
        """
        Designs a square footing for a given axial load.
        """
        # 1. Area Calculation (using Unfactored Load + 10% self-weight)
        p_service = pu_kN / 1.5
        area_req = (p_service * 1.1) / self.sbc
        side = math.ceil(math.sqrt(area_req) * 10) / 10 # Round to nearest 0.1m
        
        # 2. Net Upward Pressure (w_u)
        w_u = pu_kN / (side**2)
        
        # 3. Bending Moment at Column Face
        projection = (side - col_dim) / 2
        mu = (w_u * side * (projection**2)) / 2
        
        # 4. Depth based on Flexure (Simplified)
        # Mu = 0.138 * fck * b * d^2 (for Fe500)
        d_req = math.sqrt((mu * 10**6) / (0.138 * self.fck * (side * 1000)))
        effective_depth = math.ceil(d_req / 50) * 50 + 50 # Adding cover & rounding
        
        # 5. Area of Steel (Ast)
        # Using the standard IS 456 quadratic formula
        ast = (0.5 * self.fck / self.fy) * (1 - math.sqrt(1 - (4.6 * mu * 10**6) / (self.fck * (side * 1000) * effective_depth**2))) * (side * 1000) * effective_depth
        
        self.footings[col_id] = {
            "size_m": f"{side} x {side}",
            "depth_mm": effective_depth + 50, # Gross depth including cover
            "ast_provided_mm2": round(ast, 2),
            "rebar_suggestion": f"12mm @ {round(((side*1000) / (ast/113)), 0)}mm c/c"
        }
        return self.footings[col_id]

# Example use:
# designer = FoundationDesigner(sbc=150) # Soft soil
# result = designer.design_isolated_footing("C11", 1200) # 1200kN load
# print(result)
