import pulp

def optimize_routes(bank, depots, start_point, end_point, direct_costs, fixed_decisions, driving_times, driving_distances, max_driving_time, max_routes, distance_rate, time_rate):
    """
    Optimize routes using PuLP.
    
    Args:
        bank: The designation of the bank depot
        depots: List of depot designations to consider
        start_point: The designation of the chosen start point
        end_point: The designation of the chosen end point
        direct_costs: Dictionary mapping depot designations to direct shipment costs
        fixed_decisions: Dictionary mapping depot designations to fixed decisions made prior to the optimization
        driving_times: Dictionary mapping (depot1, depot2) tuples to driving times
        driving_distances: Dictionary mapping (depot1, depot2) tuples to driving distances
        max_driving_time: Maximum allowed driving time in minutes
        max_routes: Maximum number of routes allowed
        distance_rate: Distance cost ($/mile) for the created route
        time_rate: Time cost ($/minute) for the created route
    
    Returns:
        Dictionary with optimization results
    """
    # Create the optimization problem
    prob = pulp.LpProblem("Route_Optimization", pulp.LpMinimize)
    
    # Decision variables
    # direct_shipment[i] = 1 if depot i sends direct shipment, 0 otherwise
    direct_shipment = pulp.LpVariable.dicts("direct", depots, cat=pulp.LpBinary)
    
    # link[i,j,k] = 1 if we travel from depot i to depot j in route k, 0 otherwise
    all_locations = [bank] + depots
    all_routes = list(range(1,max_routes+1)) 
    link = pulp.LpVariable.dicts("route", [(i, j, k) for i in all_locations for j in all_locations for k in all_routes if i != j], cat=pulp.LpBinary)
    
    # u[i,k] is the position of depot i in route k (for subtour elimination)
    u = pulp.LpVariable.dicts("position", [(i,k) for i in depots for k in all_routes], lowBound=1, upBound=len(depots), cat=pulp.LpInteger)
    
    # Objective function: minimize total cost
    # Cost of direct shipments + cost of routing: time + distance
    objective = pulp.lpSum([direct_costs[i] * direct_shipment[i] for i in depots]) + \
                pulp.lpSum([( driving_times.get((i, j), 0)*time_rate + driving_distances.get((i,j), 0)*distance_rate) * link[i, j, k] for i in all_locations for j in all_locations for k in all_routes if i != j])
    prob += objective
    
    # Constraints
    
    #Honor fixed decisions
    for i in depots:
        if fixed_decisions[i] == 'Ship to bank' and i!=start_point and i!=end_point:
            prob += direct_shipment[i] == 1
        elif fixed_decisions[i] == 'Wait for pickup':
            prob += direct_shipment[i] == 0
        else: 
            0
        
    
    # Each depot is either visited or sends direct shipment
    for i in depots:
        prob += direct_shipment[i] + pulp.lpSum([link[j, i, k] for j in all_locations for k in all_routes if j != i]) == 1
    
    # Flow conservation: if a depot is visited, we must leave it
    for i in depots:
        for k in all_routes:
            prob += pulp.lpSum([link[i, j, k] for j in all_locations if j != i]) == pulp.lpSum([link[j, i, k] for j in all_locations if j != i])
    
    # The bank is left at most max_routes times
    prob += pulp.lpSum([link[bank, j, k] for j in depots for k in all_routes]) <= max_routes
    
    # The bank is reached the same number of times it is left
    prob += pulp.lpSum([link[bank, j, k] for j in depots for k in all_routes]) == pulp.lpSum([link[j, bank, k] for j in depots for k in all_routes])
    
    # Enforcing a "start_point" that is not the bank
    if start_point != bank:
        prob += pulp.lpSum([link[bank, start_point, k] for k in all_routes]) == 1
    
    # Enforcing an "end_point" that is not the bank
    if end_point != bank:
        prob += pulp.lpSum([link[end_point, bank, k] for k in all_routes]) == 1
    
    
    # Subtour elimination constraints (MTZ formulation)
    M = len(depots)
    for i in depots:
        for j in depots:
            for k in all_routes:
                if i != j:
                    prob += u[i, k] - u[j, k] + M * link[i, j, k] <= M - 1
    
    # Route time constraint
    # This is a simplification and may need to be refined for actual use
    for k in all_routes:
        prob += pulp.lpSum([driving_times.get((i, j), 0) * link[i, j, k] for i in all_locations for j in all_locations if i != j]) <= max_driving_time
    
    # Solve the problem
    prob.solve(pulp.PULP_CBC_CMD())
    
    # Check if the problem was solved successfully
    if pulp.LpStatus[prob.status] != "Optimal":
        raise Exception(f"Could not find an optimal solution. Status: {pulp.LpStatus[prob.status]}")
    
    # Extract results
    direct_shipments = {i: direct_shipment[i].value() > 0.5 for i in depots if direct_shipment[i].value() > 0.5}
    
    # Extract routes
    routes = []
    current_routes = []
    
    # Find the starting depots from the bank
    for j in depots:
        if j != start_point:
            for k in all_routes:
                if link[start_point, j, k].value() > 0.5:
                    current_routes.append([start_point, j])
        
    # Complete each route
    for route in current_routes:
        while route[-1] != end_point:
            current = route[-1]
            for j in all_locations:
                for k in all_routes:
                    if j != current and link[current, j, k].value() > 0.5:
                        route.append(j)
                        break
        routes.append(route)
    
    return {
        "direct_shipments": direct_shipments,
        "routes": routes,
        "total_cost": pulp.value(prob.objective)
    }