import streamlit as st
import numpy as np
from optimizer import Panel, optimize_layout
from visualizer import visualize_layout
import time

st.set_page_config(page_title="Panel Cut Optimizer", layout="wide")

st.title("Panel Cut Optimizer")
st.markdown("""
This tool helps you optimize the arrangement of rectangular panels on stock sheets to minimize waste.
Enter the stock sheet dimensions and the panels you need to cut below.
""")

# Stock sheet dimensions
col1, col2 = st.columns(2)
with col1:
    stock_width = st.number_input("Stock Sheet Width", min_value=1.0, value=1650.0, step=0.1)
with col2:
    stock_height = st.number_input("Stock Sheet Height", min_value=1.0, value=2140.0, step=0.1)

# Panel input section
st.subheader("Panel Specifications")
st.markdown("Add the dimensions and quantities of the panels you need to cut.")

# Initialize session state for panels and current sheet
if 'panels' not in st.session_state:
    st.session_state.panels = [{"width": 1524.0, "height": 1524.0, "quantity": 1}]
if 'current_sheet' not in st.session_state:
    st.session_state.current_sheet = 0

# Add panel button
if st.button("Add Another Panel"):
    st.session_state.panels.append({"width": 1.0, "height": 1.0, "quantity": 1})

# Panel input fields
panels = []
to_remove = None

for i, panel in enumerate(st.session_state.panels):
    col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
    with col1:
        panel['width'] = st.number_input(f"Panel {i+1} Width", 
                                       min_value=0.1, 
                                       value=float(panel['width']), 
                                       step=0.1,
                                       key=f"width_{i}")
    with col2:
        panel['height'] = st.number_input(f"Panel {i+1} Height", 
                                        min_value=0.1, 
                                        value=float(panel['height']), 
                                        step=0.1,
                                        key=f"height_{i}")
    with col3:
        panel['quantity'] = st.number_input(f"Quantity", 
                                          min_value=1, 
                                          value=int(panel['quantity']),
                                          step=1,
                                          key=f"quantity_{i}")
    with col4:
        if len(st.session_state.panels) > 1:
            if st.button("🗑️", key=f"delete_{i}"):
                to_remove = i

# Remove panel if delete button was clicked
if to_remove is not None:
    st.session_state.panels.pop(to_remove)
    st.rerun()

# Convert input to Panel objects
panels = [Panel(p['width'], p['height'], p['quantity']) for p in st.session_state.panels]

# Validate input
def validate_input(stock_width, stock_height, panels):
    for panel in panels:
        if panel.width > stock_width and panel.height > stock_width:
            return False, f"Panel size {panel.width}x{panel.height} is too large for stock width {stock_width}"
        if panel.height > stock_height and panel.width > stock_height:
            return False, f"Panel size {panel.width}x{panel.height} is too large for stock height {stock_height}"
    return True, ""

# Calculate total area for progress estimation
def calculate_total_area(panels):
    return sum(p.width * p.height * p.quantity for p in panels)

# Optimize button
if st.button("Optimize Layout"):
    try:
        # Validate input
        is_valid, error_message = validate_input(stock_width, stock_height, panels)
        if not is_valid:
            st.error(error_message)
        else:
            # Create progress bar and status
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Calculate total panel area for progress estimation
            total_area = calculate_total_area(panels)

            # Initialize calculation steps with more detail
            steps = [
                'Initializing optimization...',
                'Analyzing panel dimensions...',
                'Calculating optimal positions...',
                'Minimizing material waste...',
                'Generating visual layout...'
            ]

            for idx, step in enumerate(steps):
                status_text.text(f"Step {idx + 1}/{len(steps)}: {step}")
                progress_bar.progress((idx + 1) / len(steps))

                # Add small delay for visual feedback
                time.sleep(0.2)

                if idx == 2:  # During position calculation
                    sheets = optimize_layout(stock_width, stock_height, panels)

            # Display results
            st.subheader("Optimization Results")

            # Summary metrics
            total_area = stock_width * stock_height * len(sheets)
            used_area = sum(sum(space['w'] * space['h'] for space in sheet.used_space) 
                          for sheet in sheets)
            total_efficiency = (used_area / total_area) * 100

            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Number of Sheets", len(sheets))
            with col2:
                st.metric("Total Efficiency", f"{total_efficiency:.1f}%")
            with col3:
                st.metric("Material Waste", f"{100 - total_efficiency:.1f}%")

            # Sheet navigation
            st.subheader("Cutting Layout")
            if len(sheets) > 1:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("⬅️ Previous Sheet", 
                               disabled=st.session_state.current_sheet == 0):
                        st.session_state.current_sheet -= 1
                        st.rerun()
                with col2:
                    st.session_state.current_sheet = st.selectbox(
                        "Select Sheet",
                        range(len(sheets)),
                        format_func=lambda x: f"Sheet {x + 1}",
                        index=st.session_state.current_sheet
                    )
                with col3:
                    if st.button("Next Sheet ➡️", 
                               disabled=st.session_state.current_sheet == len(sheets) - 1):
                        st.session_state.current_sheet += 1
                        st.rerun()

            # Display current sheet details
            current_sheet = sheets[st.session_state.current_sheet]
            st.markdown(f"**Sheet {st.session_state.current_sheet + 1}** - Efficiency: {current_sheet.efficiency:.1f}%")

            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Export Current Sheet as SVG"):
                    svg_string = visualize_layout([current_sheet])
                    st.download_button(
                        label="Download SVG",
                        data=svg_string,
                        file_name=f"cutting_layout_sheet_{st.session_state.current_sheet + 1}.svg",
                        mime="image/svg+xml"
                    )
            with col2:
                if st.button("Export All Sheets as SVG"):
                    svg_string = visualize_layout(sheets)
                    st.download_button(
                        label="Download SVG",
                        data=svg_string,
                        file_name="cutting_layout_all_sheets.svg",
                        mime="image/svg+xml"
                    )

            # Display visualization
            svg_string = visualize_layout([current_sheet])
            st.markdown(f'<div style="text-align: center">{svg_string}</div>', unsafe_allow_html=True)

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

    except ValueError as e:
        st.error(f"Error: {str(e)}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error("Please check that all panel sizes can fit within the stock sheet dimensions.")