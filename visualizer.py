import matplotlib.pyplot as plt
import numpy as np
from optimizer import StockSheet
from typing import List
import io
import base64

def generate_colors(n: int) -> List[str]:
    """Generate n distinct colors for visualization."""
    return plt.cm.get_cmap('tab20')(np.linspace(0, 1, max(n, 1)))

def visualize_layout(sheets: List[StockSheet]) -> str:
    """Create a visualization of the panel layout and return as base64 encoded SVG."""
    n_sheets = len(sheets)
    fig, axs = plt.subplots(1, n_sheets, figsize=(6*n_sheets, 6))
    if n_sheets == 1:
        axs = [axs]

    # Generate unique colors for different panel sizes
    unique_sizes = set()
    for sheet in sheets:
        for space in sheet.used_space:
            unique_sizes.add((space['w'], space['h']))
    colors = dict(zip(unique_sizes, generate_colors(len(unique_sizes))))

    for idx, (sheet, ax) in enumerate(zip(sheets, axs)):
        # Draw stock sheet boundary
        ax.add_patch(plt.Rectangle((0, 0), sheet.width, sheet.height, 
                                 fill=False, color='black', linewidth=2))

        # Draw panels
        for space in sheet.used_space:
            color = colors[(space['w'], space['h'])]
            # Draw panel
            rect = plt.Rectangle((space['x'], space['y']), 
                               space['w'], space['h'],
                               fill=True, alpha=0.5, color=color)
            ax.add_patch(rect)

            # Add dimensions text
            ax.text(space['x'] + space['w']/2, space['y'] + space['h']/2,
                   f"{space['w']}x{space['h']}\n{'R' if space['panel'].rotated else ''}", 
                   ha='center', va='center', fontsize=8)

            # Draw cut lines
            ax.plot([space['x'], space['x'] + space['w']], 
                   [space['y'], space['y']], 'k--', alpha=0.5)
            ax.plot([space['x'], space['x']], 
                   [space['y'], space['y'] + space['h']], 'k--', alpha=0.5)

        ax.set_xlim(-1, sheet.width + 1)
        ax.set_ylim(-1, sheet.height + 1)
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_title(f"Sheet {idx+1}\nEfficiency: {sheet.efficiency:.1f}%")

    # Save plot to bytes buffer as SVG
    buf = io.BytesIO()
    plt.savefig(buf, format='svg', bbox_inches='tight')
    plt.close()

    # Convert to base64 string
    buf.seek(0)
    return buf.getvalue().decode('utf-8')