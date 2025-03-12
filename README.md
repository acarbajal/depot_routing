# Depot Routing Optimization Application

This application helps optimize a pickup route between depot locations and a milk bank, allowing users to minimize costs by determining which depots should be visited for pickups with an optimal route and which should send direct shipments to the bank.

## Features

- Facilitates uploading depot and driving time data via an Excel file
- Presents an interactive UI to include/exclude depots and adjust shipping costs
- Presents customizable optimization parameters (maximum driving time, gas mileage cost, staff cost)
- Optimizes routes using mixed-integer linear programming (PuLP with default solver PULP_CBC_CMD)
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
   - **Depots**: Must contain columns for "Included", "Region", "Depot Designation", "Depot Address", "Direct Shipment Cost", and "Fixed Decision"
   - **Driving Times**: Must contain columns for "Depot 1 Designation", "Depot 2 Designation", "Driving Time (minutes)", and "Driving Distance (miles)"

4. Adjust parameters in the sidebar:
   - Maximum Driving Time (hours)
   - Gas cost ($/mile)
   - Staff cost ($/hr)

5. Select which depots to include in the optimization using the checkboxes.

6. Adjust direct shipment costs and fixed decisions if necessary.

7. Click "Save Depot Information Edits" to persist any changes made to depot selection and data.

8. Select start and end point if they are different from the bank, and click "Save Start and End Points"

9. Click "Optimize Routes" to run the optimization.

10. View the results, which include direct shipments and optimized routes.

## Input File Format

The Excel file should have two sheets:

### Depots Sheet

| Included | Region | Depot Designation | Depot Address | Direct Shipment Cost | Fixed Decision    |
|----------|--------|-------------------|---------------|----------------------| ----------------- |
| Y        | North  | BANK_NORTH        | 123 Main St   | 0.00                | 'Not fixed'       |
| Y        | East   | DEPOT_EAST        | 456 Elm St    | 120.50              | 'Ship to bank'    |
| N        | West   | DEPOT_WEST        | 789 Oak St    | 150.75              | 'Wait for pickup' |

### Driving Times Sheet

| Depot 1 Designation | Depot 2 Designation | Driving Time (minutes) | Driving Distance (miles) |
|---------------------|---------------------|------------------------| ------------------------ |
| BANK_NORTH          | DEPOT_EAST          | 45.5                   | 50.4                     |
| BANK_NORTH          | DEPOT_WEST          | 60.0                   | 48.26                    |
| DEPOT_EAST          | DEPOT_WEST          | 30.25                  | 30.46                    |

## How It Works

The optimization uses a mixed-integer linear programming model to:

1. Decide which depots should send direct shipments
2. Design an optimal route to visit the remaining depots
3. Minimize the total cost while respecting constraints on:
   - Maximum driving time per route
   - Start and end points

The model ensures:

- Each depot is either visited with the route or sends a direct shipment
- Routes start and end at the specified points
- No subtours are created
- Time constraints are respected
- Fixed decisions are honored

## Dependencies

- streamlit==1.30.0
- pandas==2.1.4
- openpyxl==3.1.2
- pulp==2.7.0
