class PlotManager:
    """Calculates the legal building envelope based on Indian Building Bylaws."""
    
    def __init__(self, width, depth, city_zone="Zone_A"):
        self.plot_width = width
        self.plot_depth = depth
        self.total_area = width * depth
        
    def get_constraints(self):
        # Example NBC (National Building Code) Setbacks for residential
        if self.total_area < 200:
            return {'front': 2.0, 'rear': 1.5, 'sides': 1.0}
        else:
            return {'front': 3.0, 'rear': 2.5, 'sides': 2.0}

    def get_max_footprint(self):
        sb = self.get_constraints()
        b_width = self.plot_width - (2 * sb['sides'])
        b_depth = self.plot_depth - (sb['front'] + sb['rear'])
        
        return {
            "buildable_width": b_width,
            "buildable_depth": b_depth,
            "ground_coverage_sqm": b_width * b_depth,
            "fsi_allowed": 1.5 # Example Floor Space Index
        }

# Educational Check
my_plot = PlotManager(15.0, 20.0) # 300 sqm plot
print(f"Max Building Dimensions: {my_plot.get_max_footprint()}")
