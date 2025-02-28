# Depot Routing Optimization Application

This application helps optimize pickup routes between depot locations and a milk bank, allowing users to minimize costs by determining which depots should be visited for pickups by routes and which should send direct shipments to the bank.

## Features

- Upload depot and driving time data via an Excel file
- Interactive UI to include/exclude depots and adjust shipping costs
- Customizable optimization parameters (maximum driving time, number of routes)
- Optimizes routes using linear programming (PuLP with default solver PULP_CBC_CMD)
- Presents optimization results including:
  - Direct shipment depots and costs
  - Optimized routes with driving costs and times
  - Overall cost summary

## Project Structure

```plaintext
depot_routing/
│-- app.py                 # Main application entry point
│-- data_handler.py        # Handles file uploads and data processing
│-- optimizer.py           # Implements optimization logic
│-- ui.py                  # Manages front-end interactions
│-- requirements.txt       # Dependencies for easy installation
```

## Installation

1. Clone this repository:

```bash
   git clone <repository-url>
   cd depot_routing
   ```

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```bash
   streamlit run app.py
   ```

2. The application will open in your default web browser.

3. Upload an Excel file with two sheets:
   - **Depots**: Must contain columns for "Included", "Region", "Depot Designation", "Depot Address", and "Direct Shipment Cost"
   - **Driving Times**: Must contain columns for "Depot 1 Designation", "Depot 2 Designation", and "Driving Time (minutes)"

4. Adjust parameters in the sidebar:
   - Maximum Driving Time (hours)
   - Maximum Number of Routes

5. Select which depots to include in the optimization using the checkboxes.

6. Adjust direct shipment costs if necessary.

7. Click "Optimize Routes" to run the optimization.

8. View the results, which include direct shipments and optimized routes.

## Input File Format

The Excel file should have two sheets:

### Depots Sheet

| Included | Region | Depot Designation | Depot Address | Direct Shipment Cost |
|----------|--------|-------------------|---------------|----------------------|
| Y        | North  | BANK_NORTH        | 123 Main St   | 0.00                |
| Y        | East   | DEPOT_EAST        | 456 Elm St    | 120.50              |
| N        | West   | DEPOT_WEST        | 789 Oak St    | 150.75              |

### Driving Times Sheet

| Depot 1 Designation | Depot 2 Designation | Driving Time (minutes) |
|---------------------|---------------------|------------------------|
| BANK_NORTH          | DEPOT_EAST          | 45.5                   |
| BANK_NORTH          | DEPOT_WEST          | 60.0                   |
| DEPOT_EAST          | DEPOT_WEST          | 30.25                  |

## How It Works

The optimization uses a mixed-integer linear programming model to:

1. Decide which depots should send direct shipments
2. Design optimal routes to visit the remaining depots
3. Minimize the total cost while respecting constraints on:
   - Maximum driving time per route
   - Maximum number of routes

The model ensures:

- Each depot is either visited by a route or sends a direct shipment
- Routes start and end at the bank
- No subtours are created
- Time constraints are respected
- Fixed decisions are honored

## Dependencies

- streamlit==1.30.0
- pandas==2.1.4
- openpyxl==3.1.2
- pulp==2.7.0
