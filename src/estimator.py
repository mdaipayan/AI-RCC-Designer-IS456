class BOQEstimator:
    """Calculates the Bill of Quantities (BOQ) and estimated cost for the RCC structure."""
    
    def __init__(self, concrete_rate=5500, steel_rate=75):
        # Current average market rates in INR (can be updated)
        self.rate_concrete = concrete_rate # per m3
        self.rate_steel = steel_rate       # per kg
        self.boq_data = []
        self.totals = {"concrete_m3": 0.0, "steel_kg": 0.0, "cost_inr": 0.0}

    def add_footing(self, element_id, side_m, depth_mm, ast_mm2):
        """Calculates volume and weight for a square isolated footing."""
        depth_m = depth_mm / 1000
        
        # 1. Concrete Volume (L x B x D)
        vol_m3 = (side_m ** 2) * depth_m
        
        # 2. Steel Weight Calculation
        # Assuming steel is provided in both X and Y directions at the bottom
        # Volume of steel = Ast * Length_of_bar * 2 (directions)
        # Weight = Volume * Density (7850 kg/m3)
        steel_vol_m3 = (ast_mm2 / 1_000_000) * side_m * 2 
        steel_weight_kg = steel_vol_m3 * 7850
        
        # Log the element
        element_cost = (vol_m3 * self.rate_concrete) + (steel_weight_kg * self.rate_steel)
        self.boq_data.append({
            "Element": f"Footing {element_id}",
            "Concrete (m3)": round(vol_m3, 2),
            "Steel (kg)": round(steel_weight_kg, 2),
            "Cost (INR)": round(element_cost, 2)
        })
        
        # Add to totals
        self.totals["concrete_m3"] += vol_m3
        self.totals["steel_kg"] += steel_weight_kg
        self.totals["cost_inr"] += element_cost

    def generate_report(self):
        print(f"{'='*40}")
        print(f"ESTIMATE SUMMARY")
        print(f"{'='*40}")
        print(f"Total Concrete : {self.totals['concrete_m3']:.2f} m3")
        print(f"Total Steel    : {self.totals['steel_kg']:.2f} kg")
        print(f"Total Est. Cost: ₹{self.totals['cost_inr']:,.2f}")
        print(f"{'='*40}")
        return self.totals

# Example Usage:
# est = BOQEstimator()
# est.add_footing("C11", side_m=1.5, depth_mm=400, ast_mm2=1200)
# est.add_footing("C12", side_m=1.8, depth_mm=450, ast_mm2=1500)
# est.generate_report()
