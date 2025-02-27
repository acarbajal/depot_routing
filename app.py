# app.py
import streamlit as st
import pandas as pd
import pulp
import os
from io import BytesIO

def optimize_routes(bank, depots, direct_costs, driving_times, max_driving_time, max_routes):
    """
    Optimize routes using PuLP.
    
    Args:
        bank: The designation of the bank depot
        depots: List of depot designations to consider
        direct_costs: Dictionary mapping depot designations to direct shipment costs
        driving_times: Dictionary mapping (depot1, depot2) tuples to driving times
        max_driving_time: Maximum allowed driving time in minutes
        max_routes: Maximum number of routes allowed
    
    Returns:
        Dictionary with optimization results
    """
    # Create the optimization problem
    prob = pulp.LpProblem("Route_Optimization", pulp.LpMinimize)
    
    # Decision variables
    # x[i] = 1 if depot i sends direct shipment, 0 otherwise
    x = pulp.LpVariable.dicts("direct", depots, cat=pulp.LpBinary)
    
    # y[i,j] = 1 if we travel from depot i to depot j, 0 otherwise
    all_locations = [bank] + depots
    y = pulp.LpVariable.dicts("route", [(i, j) for i in all_locations for j in all_locations if i != j], cat=pulp.LpBinary)
    
    # u[i] is the position of depot i in the route (for subtour elimination)
    u = pulp.LpVariable.dicts("position", depots, lowBound=1, upBound=len(depots), cat=pulp.LpInteger)
    
    # Objective function: minimize total cost
    # Cost of direct shipments + cost of routing
    objective = pulp.lpSum([direct_costs[i] * x[i] for i in depots]) + \
                pulp.lpSum([driving_times.get((i, j), 0) * y[i, j] for i in all_locations for j in all_locations if i != j])
    prob += objective
    
    # Constraints
    
    # Each depot is either visited or sends direct shipment
    for i in depots:
        prob += x[i] + pulp.lpSum([y[j, i] for j in all_locations if j != i]) == 1
    
    # Flow conservation: if a depot is visited, we must leave it
    for i in depots:
        prob += pulp.lpSum([y[i, j] for j in all_locations if j != i]) == pulp.lpSum([y[j, i] for j in all_locations if j != i])
    
    # The bank is left at most max_routes times
    prob += pulp.lpSum([y[bank, j] for j in depots]) <= max_routes
    
    # The bank is reached the same number of times it is left
    prob += pulp.lpSum([y[bank, j] for j in depots]) == pulp.lpSum([y[j, bank] for j in depots])
    
    # Subtour elimination constraints (MTZ formulation)
    M = len(depots)
    for i in depots:
        for j in depots:
            if i != j:
                prob += u[i] - u[j] + M * y[i, j] <= M - 1
    
    # Route time constraint
    # This is a simplification and may need to be refined for actual use
    prob += pulp.lpSum([driving_times.get((i, j), 0) * y[i, j] for i in all_locations for j in all_locations if i != j]) <= max_driving_time
    
    # Solve the problem
    prob.solve(pulp.PULP_CBC_CMD())
    
    # Check if the problem was solved successfully
    if pulp.LpStatus[prob.status] != "Optimal":
        raise Exception(f"Could not find an optimal solution. Status: {pulp.LpStatus[prob.status]}")
    
    # Extract results
    direct_shipments = {i: x[i].value() > 0.5 for i in depots if x[i].value() > 0.5}
    
    # Extract routes
    routes = []
    current_routes = []
    
    # Find the starting depots from the bank
    for j in depots:
        if y[bank, j].value() > 0.5:
            current_routes.append([bank, j])
    
    # Complete each route
    for route in current_routes:
        while route[-1] != bank:
            current = route[-1]
            for j in all_locations:
                if j != current and y[current, j].value() > 0.5:
                    route.append(j)
                    break
        routes.append(route)
    
    return {
        "direct_shipments": direct_shipments,
        "routes": routes,
        "total_cost": pulp.value(prob.objective)
    }

def main():
    st.set_page_config(
        page_title="Route Optimization App",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Application state
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

    # Sidebar for parameters
    st.sidebar.header("Optimization Parameters")
    max_driving_time = st.sidebar.number_input("Maximum Driving Time (hours)", min_value=1, max_value=24, value=6, step=1)
    max_routes = st.sidebar.number_input("Maximum Number of Routes", min_value=1, max_value=10, value=1, step=1)

    st.title("Route Optimization Application")

    # File uploader
    uploaded_file = st.file_uploader("Upload Excel file with Depots and Driving Times", type=["xlsx"])

    if uploaded_file is not None:
        # Read Excel file
        try:
            # Read the Excel file
            depots_data = pd.read_excel(uploaded_file, sheet_name="Depots")
            driving_times_data = pd.read_excel(uploaded_file, sheet_name="Driving Times")
            
            # Validate the required columns
            required_depot_columns = ["Included", "Region", "Depot Designation", "Depot Address", "Direct Shipment Cost"]
            required_driving_times_columns = ["Depot 1 Designation", "Depot 2 Designation", "Driving Time (minutes)"]
            
            if not all(col in depots_data.columns for col in required_depot_columns):
                st.error(f"Depots tab must contain the following columns: {', '.join(required_depot_columns)}")
            elif not all(col in driving_times_data.columns for col in required_driving_times_columns):
                st.error(f"Driving Times tab must contain the following columns: {', '.join(required_driving_times_columns)}")
            else:
                # Store the data in session state
                st.session_state.depots_data = depots_data
                st.session_state.driving_times_data = driving_times_data
                
                # Initialize checkbox data from the Included column
                if not st.session_state.current_checkboxes:
                    for idx, row in depots_data.iterrows():
                        depot_designation = row["Depot Designation"]
                        included = True if row["Included"] == "Y" else False
                        st.session_state.current_checkboxes[idx] = included
                        st.session_state.current_costs[idx] = row["Direct Shipment Cost"]
                
                st.success("File uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")

    if st.session_state.depots_data is not None and st.session_state.driving_times_data is not None:
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
                col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 3, 2])
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
                
                # Create checkboxes and input fields
                for idx, row in edited_depots.iterrows():
                    current_checkbox = st.session_state.current_checkboxes.get(idx, False)
                    if st.session_state.show_all_depots or current_checkbox:
                        col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 3, 2])
                        
                        with col1:
                            checkbox_value = st.checkbox(
                                label="", 
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
                                "",
                                value=float(st.session_state.current_costs.get(idx, row["Direct Shipment Cost"])),
                                key=f"cost_{idx}",
                                step=0.01
                            )
                            st.session_state.current_costs[idx] = cost_value
            
            submitted = st.form_submit_button("Save Changes")
        
        if submitted:
            # Update the dataframe with the new values
            for idx in st.session_state.current_checkboxes:
                if idx < len(edited_depots):
                    edited_depots.at[idx, "Included"] = "Y" if st.session_state.current_checkboxes[idx] else "N"
                    edited_depots.at[idx, "Direct Shipment Cost"] = st.session_state.current_costs[idx]
            
            st.session_state.depots_data = edited_depots
            st.success("Changes saved successfully!")
        
        # Button to start optimization
        if st.button("Optimize Routes"):
            # Prepare data for optimization
            # Get only the included depots (based on current checkboxes)
            included_indices = [idx for idx, checked in st.session_state.current_checkboxes.items() if checked]
            included_depots = edited_depots.loc[included_indices]
            
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
            bank = edited_depots.iloc[0]["Depot Designation"]
            
            # Get depot designations for included depots
            included_depot_designations = included_depots["Depot Designation"].tolist()
            
            # Remove bank from list if it's there, as we handle it separately
            if bank in included_depot_designations:
                included_depot_designations.remove(bank)
            
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
                st.session_state.driving_times = driving_times  # Store for displaying results
                st.session_state.direct_costs = direct_costs    # Store for displaying results
            except Exception as e:
                st.error(f"Optimization error: {e}")
        
        # Display optimization results
        if st.session_state.optimization_results is not None:
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

# Run the app
if __name__ == "__main__":
    main()