"""
PuLP Optimization Example for Product Mix Problem

A company manufactures three products (X, Y, and Z) using two resources (labor and materials).
Each unit of X requires 2 hours of labor and 1 kg of material.
Each unit of Y requires 1 hour of labor and 3 kg of material.
Each unit of Z requires 3 hours of labor and 2 kg of material.
The company has 100 hours of labor and 90 kg of material available per day.
The profit is $40 per unit for X, $30 per unit for Y, and $50 per unit for Z.
How many units of each product should be produced to maximize profit?
"""

import pulp

# Create the optimization model
model = pulp.LpProblem(name="Product_Mix_Problem", sense=pulp.LpMaximize)

# Define decision variables
# Non-negative continuous variables for the number of units of each product to produce
X = pulp.LpVariable(name="X", lowBound=0, cat=pulp.LpContinuous)
Y = pulp.LpVariable(name="Y", lowBound=0, cat=pulp.LpContinuous)
Z = pulp.LpVariable(name="Z", lowBound=0, cat=pulp.LpContinuous)

# Define the objective function (maximize profit)
model += 40 * X + 30 * Y + 50 * Z, "Total_Profit"

# Define the constraints
# Labor constraint: 2X + 1Y + 3Z ≤ 100 hours
model += 2 * X + 1 * Y + 3 * Z <= 100, "Labor_Constraint"

# Material constraint: 1X + 3Y + 2Z ≤ 90 kg
model += 1 * X + 3 * Y + 2 * Z <= 90, "Material_Constraint"

# Solve the model
status = model.solve()

# Print the results
print(f"Status: {pulp.LpStatus[status]}")

# Check if the model was successfully solved
if status == pulp.LpStatusOptimal:
    print("\nOptimal Solution:")
    print(f"X = {X.value():.2f} units")
    print(f"Y = {Y.value():.2f} units")
    print(f"Z = {Z.value():.2f} units")
    print(f"\nMaximum Profit: ${pulp.value(model.objective):.2f}")
    
    # Print the constraint utilization
    print("\nResource Utilization:")
    labor_used = 2 * X.value() + 1 * Y.value() + 3 * Z.value()
    material_used = 1 * X.value() + 3 * Y.value() + 2 * Z.value()
    print(f"Labor used: {labor_used:.2f} hours out of 100 hours ({labor_used/100*100:.1f}%)")
    print(f"Material used: {material_used:.2f} kg out of 90 kg ({material_used/90*100:.1f}%)")
else:
    print("No optimal solution found.") 