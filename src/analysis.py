class LoadTakedown:
    def __init__(self, planner_obj, concrete_density=25.0, brick_density=19.0):
        self.grid = planner_obj
        self.gamma_c = concrete_density # kN/m3
        self.gamma_b = brick_density    # kN/m3
        self.loads = {} # Store loads per column ID

    def calculate_column_loads(self, slab_thickness=0.150, wall_height=3.0):
        """
        Calculates axial load based on tributary areas.
        """
        spacing_x = self.grid.grid_data['spacing_x']
        spacing_y = self.grid.grid_data['spacing_y']
        trib_area = spacing_x * spacing_y
        
        # 1. Slab Load (DL + LL)
        # DL = thickness * density, LL = 2.0, Finish = 1.0
        unit_slab_load = (slab_thickness * self.gamma_c) + 1.0 + 2.0
        
        # 2. Wall Load (Running meter load transferred to columns)
        # Assumes walls run along all beams
        wall_load_per_m = 0.230 * wall_height * self.gamma_b # 230mm brick wall
        
        for col in self.grid.columns:
            # Interior columns take full trib_area, corners take 1/4th, edges take 1/2
            # For educational simplicity, we use the full bay area multiplier
            total_axial_load = (unit_slab_load * trib_area) + (wall_load_per_m * (spacing_x + spacing_y))
            
            # Multiply by number of floors (e.g., Duplex = 2 floors)
            total_design_load = total_axial_load * self.grid.floors
            
            # Apply Factor of Safety (Limit State of Collapse) = 1.5
            pu = total_design_load * 1.5
            
            self.loads[col['id']] = {
                'unfactored_kN': round(total_design_load, 2),
                'factored_pu_kN': round(pu, 2)
            }
        return self.loads

# Integration Example
# loads = LoadTakedown(plan).calculate_column_loads()
# print(f"Load on central column: {loads['C11']['factored_pu_kN']} kN")
