import numpy as np
from typing import List, Tuple, Dict

class Panel:
    def __init__(self, width: float, height: float, quantity: int):
        self.width = width
        self.height = height
        self.quantity = quantity
        self.position: Tuple[float, float] | None = None
        self.rotated = False

class StockSheet:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        self.used_space = []
        self.efficiency = 0.0

def find_position(sheet: StockSheet, panel: Panel) -> Tuple[bool, float, float, bool]:
    """Find the best position for a panel on the sheet using optimized algorithm."""
    best_x = float('inf')
    best_y = float('inf')
    can_place = False
    best_rotated = False

    # Calculate step size based on panel dimensions (0.1% of smallest dimension)
    step = min(panel.width, panel.height, sheet.width, sheet.height) * 0.001

    # Try both orientations
    orientations = [(panel.width, panel.height, False)]
    if panel.width != panel.height:
        orientations.append((panel.height, panel.width, True))

    # Sort orientations to prefer the one that better fits the available space
    orientations.sort(key=lambda x: (
        -(x[0] if x[0] <= sheet.width else 0),  # Prefer wider pieces along width
        -(x[1] if x[1] <= sheet.height else 0)  # Prefer taller pieces along height
    ))

    for w, h, rotated in orientations:
        # Skip if panel doesn't fit in this orientation
        if w > sheet.width or h > sheet.height:
            continue

        # First try corners and edges
        priority_positions = [
            (0, 0),  # Bottom-left corner
            (sheet.width - w, 0),  # Bottom-right corner
            (0, sheet.height - h),  # Top-left corner
            (sheet.width - w, sheet.height - h),  # Top-right corner
        ]

        # Add positions next to existing panels
        for used in sheet.used_space:
            priority_positions.extend([
                (used['x'] + used['w'], used['y']),  # Right side
                (used['x'], used['y'] + used['h']),  # Top side
            ])

        # Filter valid priority positions
        priority_positions = [
            (x, y) for x, y in priority_positions
            if 0 <= x <= sheet.width - w and 0 <= y <= sheet.height - h
        ]

        # Check priority positions first
        for x, y in priority_positions:
            valid = True
            for used in sheet.used_space:
                if not (x + w <= used['x'] or x >= used['x'] + used['w'] or
                       y + h <= used['y'] or y >= used['y'] + used['h']):
                    valid = False
                    break

            if valid:
                if not can_place or (y < best_y or (y == best_y and x < best_x)):
                    best_x = x
                    best_y = y
                    can_place = True
                    best_rotated = rotated

        # If no priority position works, try regular positions with optimized step size
        if not can_place:
            for x in np.arange(0, sheet.width - w + step, step):
                for y in np.arange(0, sheet.height - h + step, step):
                    valid = True
                    for used in sheet.used_space:
                        if not (x + w <= used['x'] or x >= used['x'] + used['w'] or
                               y + h <= used['y'] or y >= used['y'] + used['h']):
                            valid = False
                            break

                    if valid:
                        if not can_place or (y < best_y or (y == best_y and x < best_x)):
                            best_x = x
                            best_y = y
                            can_place = True
                            best_rotated = rotated

    return can_place, best_x, best_y, best_rotated

def optimize_layout(stock_width: float, stock_height: float, panels: List[Panel]) -> List[StockSheet]:
    """Optimize the layout of panels on stock sheets."""
    # Create copies of panels and sort by area and longer dimension
    panels_copy = []
    for panel in panels:
        for _ in range(panel.quantity):
            panels_copy.append(Panel(panel.width, panel.height, 1))

    # Sort panels by longer dimension first
    panels_copy.sort(key=lambda p: (
        -max(p.width, p.height),  # Longer dimension first
        -(p.width * p.height),    # Then by area
        -min(p.width, p.height)   # Finally by shorter dimension
    ))

    sheets = [StockSheet(stock_width, stock_height)]
    remaining_panels = panels_copy

    while remaining_panels:
        panel = remaining_panels[0]
        placed = False

        # Try to place panel on existing sheets
        for sheet in sheets:
            can_place, x, y, rotated = find_position(sheet, panel)
            if can_place:
                w = panel.height if rotated else panel.width
                h = panel.width if rotated else panel.height
                sheet.used_space.append({
                    'x': x, 'y': y, 'w': w, 'h': h, 
                    'panel': panel
                })
                panel.position = (x, y)
                panel.rotated = rotated
                panel.quantity -= 1
                placed = True
                break

        # If panel couldn't be placed, create new sheet
        if not placed:
            new_sheet = StockSheet(stock_width, stock_height)
            can_place, x, y, rotated = find_position(new_sheet, panel)
            if can_place:
                w = panel.height if rotated else panel.width
                h = panel.width if rotated else panel.height
                new_sheet.used_space.append({
                    'x': x, 'y': y, 'w': w, 'h': h, 
                    'panel': panel
                })
                panel.position = (x, y)
                panel.rotated = rotated
                panel.quantity -= 1
                sheets.append(new_sheet)
            else:
                raise ValueError(f"Panel {panel.width}x{panel.height} is too large for stock sheet {stock_width}x{stock_height}")

        # Remove panel if all quantities placed
        if panel.quantity == 0:
            remaining_panels.pop(0)

    # Calculate efficiency for each sheet
    for sheet in sheets:
        used_area = sum(space['w'] * space['h'] for space in sheet.used_space)
        sheet.efficiency = (used_area / (sheet.width * sheet.height)) * 100

    return sheets