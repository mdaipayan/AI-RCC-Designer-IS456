import numpy as np

class StructuralGrid:
    def __init__(self, buildable_w, buildable_d):
        self.w = buildable_w
        self.d = buildable_d
        self.columns = []

    def generate_grid(self, min_span=3.0, max_span=5.0):
        """
        Divide the building width and depth into equal spans 
        between min and max limits.
        """
        # Calculate number of bays for Width
        n_bays_w = int(np.ceil(self.w / max_span))
        span_w = self.w / n_bays_w
        
        # Calculate number of bays for Depth
        n_bays_d = int(np.ceil(self.d / max_span))
        span_d = self.d / n_bays_d
        
        # Create coordinates for columns (Nodes)
        for i in range(n_bays_w + 1):
            for j in range(n_bays_d + 1):
                self.columns.append((round(i * span_w, 2), round(j * span_d, 2)))
        
        return {
            "columns": self.columns,
            "span_x": span_w,
            "span_y": span_d,
            "total_columns": len(self.columns)
        }

# Example: A 9m x 12m buildable area
grid = StructuralGrid(9.0, 12.0)
layout = grid.generate_grid()
print(f"Generated {layout['total_columns']} columns with spans: {layout['span_x']}m x {layout['span_y']}m")
