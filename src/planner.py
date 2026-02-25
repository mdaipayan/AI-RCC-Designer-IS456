import numpy as np
import matplotlib.pyplot as plt

class BuildingPlanner:
    def __init__(self, width, depth, floors=2):
        self.width = width
        self.depth = depth
        self.floors = floors
        self.columns = []
        self.grid_data = {}

    def generate_structural_grid(self, max_span=4.5):
        """
        Creates a grid of columns based on maximum allowable beam spans (IS 456).
        """
        # Calculate number of segments
        nx = int(np.ceil(self.width / max_span))
        ny = int(np.ceil(self.depth / max_span))
        
        # Calculate precise spacing
        spacing_x = self.width / nx
        spacing_y = self.depth / ny
        
        # Generate Column Coordinates
        for i in range(nx + 1):
            for j in range(ny + 1):
                self.columns.append({
                    'id': f"C{i}{j}",
                    'pos': (round(i * spacing_x, 2), round(j * spacing_y, 2)),
                    'is_staircase_boundary': False
                })
        
        self.grid_data = {'spacing_x': spacing_x, 'spacing_y': spacing_y, 'nx': nx, 'ny': ny}
        return self.columns

    def assign_staircase(self):
        """
        In a Duplex, the staircase is a fixed structural element.
        We assign it to a central-side bay to ensure accessibility.
        """
        # Logic: Pick a bay near the middle of the depth
        stair_bay_id = f"C0{self.grid_data['ny'] // 2}" 
        return stair_bay_id

    def visualize_plan(self):
        plt.figure(figsize=(8, 10))
        x_coords = [c['pos'][0] for c in self.columns]
        y_coords = [c['pos'][1] for c in self.columns]
        
        # Plot columns as RCC sections
        plt.scatter(x_coords, y_coords, color='black', marker='s', s=150, label='RCC Columns')
        
        # Draw Centerline Beams
        for i in range(self.grid_data['nx'] + 1):
            plt.plot([i * self.grid_data['spacing_x']] * 2, [0, self.depth], 'gray', linestyle='--')
        for j in range(self.grid_data['ny'] + 1):
            plt.plot([0, self.width], [j * self.grid_data['spacing_y']] * 2, 'gray', linestyle='--')
            
        plt.title(f"AI Generated Structural Centerline - {self.floors} Storey Duplex")
        plt.gca().set_aspect('equal', adjustable='box')
        plt.xlabel("Width (m)")
        plt.ylabel("Depth (m)")
        plt.legend()
        plt.show()

# Testing the logic
plan = BuildingPlanner(width=9.0, depth=12.0)
plan.generate_structural_grid()
plan.visualize_plan()
