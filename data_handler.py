import pandas as pd
import streamlit as st

def read_excel_data(uploaded_file):
    """
    Read and validate Excel file with depots and driving times data.
    
    Args:
        uploaded_file: The uploaded Excel file object
    
    Returns:
        Tuple containing (success, message, depots_data, driving_times_data)
    """
    try:
        # Read the Excel file
        depots_data = pd.read_excel(uploaded_file, sheet_name="Depots")
        driving_times_data = pd.read_excel(uploaded_file, sheet_name="Driving Times")
        
        # Validate the data
        validation_result = validate_data(depots_data, driving_times_data)
        
        if validation_result[0]:
            return True, "Data validated successfully", depots_data, driving_times_data
        else:
            return False, validation_result[1], None, None
            
    except Exception as e:
        return False, f"Error reading Excel file: {e}", None, None

def validate_data(depots_data, driving_times_data):
    """
    Validate that the uploaded data contains all required columns.
    
    Args:
        depots_data: DataFrame containing depot information
        driving_times_data: DataFrame containing driving times
    
    Returns:
        Tuple containing (success, error_message)
    """
    required_depot_columns = ["Included", "Region", "Depot Designation", "Depot Address", "Direct Shipment Cost"]
    required_driving_times_columns = ["Depot 1 Designation", "Depot 2 Designation", "Driving Time (minutes)"]
    
    if not all(col in depots_data.columns for col in required_depot_columns):
        return False, f"Depots tab must contain the following columns: {', '.join(required_depot_columns)}"
    elif not all(col in driving_times_data.columns for col in required_driving_times_columns):
        return False, f"Driving Times tab must contain the following columns: {', '.join(required_driving_times_columns)}"
    
    return True, "Data validation successful"

def prepare_optimization_data(included_depot_indices, depots_data, driving_times_data):
    """
    Prepare data for optimization based on selected depots.
    
    Args:
        included_depot_indices: List of indices of included depots
        depots_data: DataFrame containing depot information
        driving_times_data: DataFrame containing driving times
    
    Returns:
        Dictionary containing prepared data for optimization
    """
    # Get included depots
    included_depots = depots_data.loc[included_depot_indices]
    
    # Create cost dictionary
    direct_costs = {}
    for idx, row in included_depots.iterrows():
        direct_costs[row["Depot Designation"]] = st.session_state.current_costs[idx]
    
    # Create driving times dictionary
    driving_times = {}
    for idx, row in driving_times_data.iterrows():
        depot1 = row["Depot 1 Designation"]
        depot2 = row["Depot 2 Designation"]
        time = float(row["Driving Time (minutes)"])
        driving_times[(depot1, depot2)] = time
        # Ensure symmetry if not already provided
        if (depot2, depot1) not in driving_times:
            driving_times[(depot2, depot1)] = time
    
    # Identify the bank (first depot in the list)
    bank = depots_data.iloc[0]["Depot Designation"]
    
    # Get depot designations for included depots
    included_depot_designations = included_depots["Depot Designation"].tolist()
    
    # Remove bank from list if it's there, as we handle it separately
    if bank in included_depot_designations:
        included_depot_designations.remove(bank)
    
    return {
        "bank": bank,
        "depots": included_depot_designations,
        "direct_costs": direct_costs,
        "driving_times": driving_times
    }