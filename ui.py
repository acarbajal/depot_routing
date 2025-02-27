import streamlit as st
import pandas as pd

def setup_page_config():
    """Set up the Streamlit page configuration."""
    st.set_page_config(
        page_title="Route Optimization App",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def display_sidebar():
    """
    Display sidebar with optimization parameters.
    
    Returns:
        Tuple of (max_driving_time, max_routes)
    """
    st.sidebar.header("Optimization Parameters")
    max_driving_time = st.sidebar.number_input("Maximum Driving Time (hours)", min_value=1, max_value=24, value=6, step=1)
    max_routes = st.sidebar.number_input("Maximum Number of Routes", min_value=1, max_value=10, value=1, step=1)
    
    return max_driving_time, max_routes

def display_depots_form():
    """Display and handle the depots data form."""
    # Toggle for showing all depots
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Show All Depots"):
            st.session_state.show_all_depots = True
    
    with col2:
        if st.button("Hide Unselected Depots"):
            st.session_state.show_all_depots = False
    
    # Display depots data with editable checkboxes
    st.subheader("Depots Data")
    
    # Create a copy of the dataframe to avoid modification warnings
    edited_depots = st.session_state.depots_data.copy()
    
    # Display the data in a form
    with st.form("depot_form"):
        # Create a container for the form fields
        form_container = st.container()
        
        # Display form fields
        with form_container:
            
             # Create header row
            col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 3, 3, 2, 2])
            with col1:
                st.write("**Include**")
            with col2:
                st.write("**Region**")
            with col3:
                st.write("**Designation**")
            with col4:
                st.write("**Address**")
            with col5:
                st.write("**Direct Shipping Cost**")
            with col6:
                st.write('**Fixed Decision**')
            
            # Create checkboxes and input fields
            for idx, row in edited_depots.iterrows():
                current_checkbox = st.session_state.current_checkboxes.get(idx, False)
                if st.session_state.show_all_depots or current_checkbox:
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 3, 3, 2, 2])
                    
                    with col1:
                        checkbox_value = st.checkbox(
                            label="Included?",
                            label_visibility = "hidden", 
                            value=current_checkbox, 
                            key=f"cb_{idx}"
                        )
                        st.session_state.current_checkboxes[idx] = checkbox_value
                    
                    with col2:
                        st.text(row["Region"])
                    
                    with col3:
                        st.text(row["Depot Designation"])
                    
                    with col4:
                        st.text(row["Depot Address"])
                    
                    with col5:
                        cost_value = st.number_input(
                            label = "direct shipping cost",
                            label_visibility = "hidden",
                            value=float(st.session_state.current_costs.get(idx, row["Direct Shipment Cost"])),
                            key=f"cost_{idx}",
                            step=0.01
                        )
                        st.session_state.current_costs[idx] = cost_value
                    
                    with col6:
                        option_values = ['Not fixed', 'Ship to bank', 'Wait for pickup']
                        
                        current_fixed_decision = st.session_state.current_fixed_decisions.get(idx, 'Not fixed')

                        fixed_decision_value = st.selectbox(
                            label="fixed decision",
                            label_visibility="hidden",
                            options = option_values,
                            index = option_values.index(current_fixed_decision),
                            key=f"fixed_{idx}"
                        )
                        st.session_state.current_fixed_decisions[idx] = fixed_decision_value
        
        submitted = st.form_submit_button("Save Changes")
    
    if submitted:
        # Update the dataframe with the new values
        for idx in st.session_state.current_checkboxes:
            if idx < len(edited_depots):
                edited_depots.at[idx, "Included"] = "Y" if st.session_state.current_checkboxes[idx] else "N"
                edited_depots.at[idx, "Direct Shipment Cost"] = st.session_state.current_costs[idx]
                edited_depots.at[idx, "Fixed Decision"] = st.session_state.current_fixed_decisions[idx]
        
        st.session_state.depots_data = edited_depots
        st.success("Changes saved successfully!")

def display_optimization_results():
    """Display optimization results."""
    st.subheader("Optimization Results")
    
    direct_shipments = st.session_state.optimization_results["direct_shipments"]
    routes = st.session_state.optimization_results["routes"]
    total_cost = st.session_state.optimization_results["total_cost"]
    driving_times = st.session_state.driving_times
    direct_costs = st.session_state.direct_costs
    
    # Display direct shipments in a table
    st.write("### Depots that will send direct shipments:")
    if direct_shipments:
        direct_data = {
            "Depot Designation": list(direct_shipments.keys()),
            "Direct Shipment Cost ($)": [direct_costs[depot] for depot in direct_shipments]
        }
        direct_df = pd.DataFrame(direct_data)
        st.table(direct_df)
        
        direct_total = sum(direct_costs[depot] for depot in direct_shipments)
        st.write(f"**Total direct shipment cost:** ${direct_total:.2f}")
    else:
        st.write("No depots will send direct shipments.")
    
    # Display routes in tables
    st.write("### Routes to visit depots:")
    
    for i, route in enumerate(routes):
        st.write(f"**Route {i+1}:**")
        
        # Create route data with driving costs
        route_data = []
        total_driving_cost = 0
        
        for j in range(len(route)):
            if j == 0:
                # First stop has no driving cost from previous
                route_data.append({
                    "Depot Designation": route[j],
                    "Driving Cost ($)": ""
                })
            else:
                # Calculate driving cost from previous depot
                from_depot = route[j-1]
                to_depot = route[j]
                driving_cost = driving_times.get((from_depot, to_depot), 0)
                total_driving_cost += driving_cost
                
                route_data.append({
                    "Depot Designation": to_depot,
                    "Driving Cost ($)": f"{driving_cost:.2f}"
                })
        
        # Create and display the route table
        route_df = pd.DataFrame(route_data)
        st.table(route_df)
        
        # Calculate and display route time
        route_time = 0
        for j in range(len(route) - 1):
            depot1 = route[j]
            depot2 = route[j + 1]
            if (depot1, depot2) in driving_times:
                route_time += driving_times[(depot1, depot2)]
        
        st.write(f"**Route {i+1} driving time:** {route_time:.2f} minutes ({route_time/60:.2f} hours)")
        st.write(f"**Route {i+1} total driving cost:** ${total_driving_cost:.2f}")
        st.write("---")
    
    st.write(f"### Overall total cost: ${total_cost:.2f}")