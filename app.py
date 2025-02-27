import streamlit as st
from data_handler import read_excel_data, validate_data
from optimizer import optimize_routes
from ui import setup_page_config, display_sidebar, display_depots_form, display_optimization_results

def main():
    # Set up the page configuration
    setup_page_config()

    # Application state initialization
    if 'depots_data' not in st.session_state:
        st.session_state.depots_data = None
    if 'driving_times_data' not in st.session_state:
        st.session_state.driving_times_data = None
    if 'show_all_depots' not in st.session_state:
        st.session_state.show_all_depots = False
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None
    if 'current_checkboxes' not in st.session_state:
        st.session_state.current_checkboxes = {}
    if 'current_costs' not in st.session_state:
        st.session_state.current_costs = {}
    if 'driving_times' not in st.session_state:
        st.session_state.driving_times = {}
    if 'direct_costs' not in st.session_state:
        st.session_state.direct_costs = {}

    # Sidebar for parameters
    max_driving_time, max_routes = display_sidebar()

    st.title("Route Optimization Application")

    # File uploader
    uploaded_file = st.file_uploader("Upload Excel file with Depots and Driving Times", type=["xlsx"])

    if uploaded_file is not None:
        # Read and validate Excel file
        success, message, depots_data, driving_times_data = read_excel_data(uploaded_file)
        
        if success:
            # Store the data in session state
            st.session_state.depots_data = depots_data
            st.session_state.driving_times_data = driving_times_data
            
            # Initialize checkbox data from the Included column if not already initialized
            if not st.session_state.current_checkboxes:
                for idx, row in depots_data.iterrows():
                    depot_designation = row["Depot Designation"]
                    included = True if row["Included"] == "Y" else False
                    st.session_state.current_checkboxes[idx] = included
                    st.session_state.current_costs[idx] = row["Direct Shipment Cost"]
            
            st.success("File uploaded successfully!")
        else:
            st.error(message)

    if st.session_state.depots_data is not None and st.session_state.driving_times_data is not None:
        # Display the depots form
        display_depots_form()
        
        # Button to start optimization
        if st.button("Optimize Routes"):
            # Prepare data for optimization
            # Get only the included depots (based on current checkboxes)
            included_indices = [idx for idx, checked in st.session_state.current_checkboxes.items() if checked]
            included_depots = st.session_state.depots_data.loc[included_indices]
            
            # Create cost dictionary
            direct_costs = {}
            for idx, row in included_depots.iterrows():
                direct_costs[row["Depot Designation"]] = st.session_state.current_costs[idx]
            
            # Create driving times dictionary
            driving_times = {}
            for idx, row in st.session_state.driving_times_data.iterrows():
                depot1 = row["Depot 1 Designation"]
                depot2 = row["Depot 2 Designation"]
                time = float(row["Driving Time (minutes)"])
                driving_times[(depot1, depot2)] = time
                # Ensure symmetry if not already provided
                if (depot2, depot1) not in driving_times:
                    driving_times[(depot2, depot1)] = time
            
            # Identify the bank (first depot in the list)
            bank = st.session_state.depots_data.iloc[0]["Depot Designation"]
            
            # Get depot designations for included depots
            included_depot_designations = included_depots["Depot Designation"].tolist()
            
            # Remove bank from list if it's there, as we handle it separately
            if bank in included_depot_designations:
                included_depot_designations.remove(bank)
            
            # Store for displaying results
            st.session_state.driving_times = driving_times
            st.session_state.direct_costs = direct_costs
            
            # Perform optimization
            try:
                results = optimize_routes(
                    bank,
                    included_depot_designations,
                    direct_costs,
                    driving_times,
                    max_driving_time * 60,  # Convert to minutes
                    max_routes
                )
                st.session_state.optimization_results = results
            except Exception as e:
                st.error(f"Optimization error: {e}")
        
        # Display optimization results
        if st.session_state.optimization_results is not None:
            display_optimization_results()

# Run the app
if __name__ == "__main__":
    main()