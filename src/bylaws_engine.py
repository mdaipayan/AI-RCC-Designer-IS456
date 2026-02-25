class BuildingBylaws:
    def __init__(self, plot_width, plot_depth, building_type="Residential"):
        self.w = plot_width
        self.d = plot_depth
        self.type = building_type

    def get_setbacks(self):
        """Standard setbacks based on plot size (Example values)"""
        if self.w * self.d < 250: # Plots < 250 sqm
            return {'front': 3.0, 'rear': 2.0, 'sides': 1.5}
        else:
            return {'front': 4.5, 'rear': 3.0, 'sides': 2.0}

    def calculate_footprint(self):
        sb = self.get_setbacks()
        effective_w = self.w - (2 * sb['sides'])
        effective_d = self.d - (sb['front'] + sb['rear'])
        
        if effective_w <= 0 or effective_d <= 0:
            return "Plot too small for standard setbacks."
            
        return {
            "max_width": round(effective_w, 2),
            "max_depth": round(effective_d, 2),
            "area": round(effective_w * effective_d, 2)
        }

# Educational Example:
plot = BuildingBylaws(12.0, 18.0) # A standard 40x60 ft plot approx
print(f"Buildable Footprint: {plot.calculate_footprint()}")
