import pulp

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
    # direct_shipment[i] = 1 if depot i sends direct shipment, 0 otherwise
    direct_shipment = pulp.LpVariable.dicts("direct", depots, cat=pulp.LpBinary)
    
    # link[i,j,k] = 1 if we travel from depot i to depot j in route k, 0 otherwise
    all_locations = [bank] + depots
    all_routes = list(range(1,max_routes+1)) 
    link = pulp.LpVariable.dicts("route", [(i, j, k) for i in all_locations for j in all_locations for k in all_routes if i != j], cat=pulp.LpBinary)
    
    # u[i,k] is the position of depot i in route k (for subtour elimination)
    u = pulp.LpVariable.dicts("position", [(i,k) for i in depots for k in all_routes], lowBound=1, upBound=len(depots), cat=pulp.LpInteger)
    
    # Objective function: minimize total cost
    # Cost of direct shipments + cost of routing
    objective = pulp.lpSum([direct_costs[i] * direct_shipment[i] for i in depots]) + \
                pulp.lpSum([driving_times.get((i, j), 0) * link[i, j, k] for i in all_locations for j in all_locations for k in all_routes if i != j])
    prob += objective
    
    # Constraints
    
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
        for k in all_routes:
            if link[bank, j, k].value() > 0.5:
                current_routes.append([bank, j])
    
    # Complete each route
    for route in current_routes:
        while route[-1] != bank:
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