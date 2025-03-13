from gurobipy import Model, GRB, quicksum, LinExpr
import time

class ExactAlgorithm:
    def __init__(self, problem):
        self.problem = problem
        self.model = None
        self.columns = {}

        for t in self.problem.timePeriods:
            self.columns[t] = {}
        for s in self.problem.shipments:
            self.columns[s.month][s.shipmentId] = []

    def solve(self):
        self.initialize_RMP()

        self.model.setParam('OutputFlag', 1)  # Enable Gurobi output

        self.model.optimize()

        # Print only the y variables (OpenWarehouse variables) with value 1

        isBoolean = True
        for v in self.model.getVars():
            if v.VarName.startswith('Open'):
                print(f"{v.VarName} = {v.X}")

            if (v.varName.endswith('ES50') or v.varName.endswith('PL46')) and v.X > 0.005:
                print(f"{v.VarName} = {v.X}")
                isBoolean = False

            if (v.varName.endswith('TR59')) and v.X > 0.005:
                print(f"{v.VarName} = {v.X}")

        print('-------------------')

        if isBoolean:
            print('No shipment through Spain and Poland')

        print('----------------')

        return self.model.ObjVal

    def initialize_RMP(self):
        self.model = Model("SPP")
        start_time = time.time()
        self.findTildeCost()
        end_time = time.time()

        print(f"findTildeCost execution time: {end_time - start_time:.6f} seconds")

        # Decision variables
        x = {}  # Binary decision variable for route selection
        y = {}  # Binary decision variable for warehouse selection

        for t in self.columns:
            for s in self.columns[t]:
                for cost, wh in self.columns.get(t, {}).get(s, []):
                    x[(wh, s)] = self.model.addVar(vtype=GRB.BINARY, obj=cost, name=f"x_{wh}_{s}")

        for warehouse in self.problem.warehouses:
            y[warehouse] = self.model.addVar(vtype=GRB.BINARY, obj=warehouse.openingCost,  name=f"y_{warehouse.warehouseId}")

        # Constraint 1: Each shipment must be assigned to exactly one route
        for s in self.problem.shipments:
            lhs_expr = quicksum(
                x[(r, s.shipmentId)]
                for t in self.problem.timePeriods
                for cost, r in self.columns.get(t, {}).get(s.shipmentId, [])
            )
            self.model.addConstr(lhs_expr == 1, name=f"shipment_{s.shipmentId}")

        for t in self.problem.timePeriods:
            lhs_expr = quicksum(
                s.weight * x[(r, s.shipmentId)]
                for s in self.problem.shipments
                for cost, r in self.columns.get(t, {}).get(s.shipmentId, [])
                if r == "CH01"
            )
            self.model.addConstr(lhs_expr <= 250000, name=f"capacity_t_{t}")


            # Constraint 3: Warehouse capacity constraint
        for warehouse in self.problem.warehouses:
            for t in self.problem.timePeriods:
                lhs_expr = quicksum(
                    s.weight * x[(r, s.shipmentId)]
                    for s in self.problem.shipments
                    for cost, r in self.columns.get(t, {}).get(s.shipmentId, [])
                    if r == warehouse.warehouseId
                )
                self.model.addConstr(
                    lhs_expr <= warehouse.capacity * y[warehouse],
                    name=f"wh_{warehouse}_t_{t}"
                )

        self.model.update()

        # self.createEmptyModel()

    def findTildeCost(self):
        for shipment in self.problem.shipments:
            country = shipment.country
            postalCode = shipment.postalCode
            startPoint = shipment.startingPoint
            weight = shipment.weight
            dangerous = shipment.isDangerous
            isPickUp = shipment.isPickUp

            if startPoint == "CH01":
                if isPickUp:
                    tildeCost = 0
                else:
                    tildeCost = self.calculateCostBetweenPoints(country, postalCode, startPoint, weight, dangerous)
                self.columns[shipment.month][shipment.shipmentId].append([tildeCost, startPoint])

                self.findWarehousePair(shipment, country, postalCode, startPoint, weight, dangerous, isPickUp)
            else:
                self.findWarehousePair(shipment, country, postalCode, startPoint, weight, dangerous, isPickUp)

    def createEmptyModel(self):
        for shipment in self.problem.shipments:
            self.model.addConstr(LinExpr() == 1, name=f"CoverShipment_{shipment.shipmentId}")

        for t in self.problem.timePeriods:
            # Define an empty linear expression (though it should ideally have variables)
            prod_constr = self.model.addConstr(
                LinExpr() <= 250000,
                name=f"ProductionCapacity_CH01_T{t}"
            )

            # 3) Warehouse-opening variables and constraints
            # We do:  sum_{shipments} (weight_s*x_r) - capacity*y_var <= 0

        for warehouse in self.problem.warehouses:
            # y_var in [0,1] in LP relaxation, with cost = warehouse.openingCost
            y_var = self.model.addVar(
                lb=0,
                ub=1,
                vtype=GRB.BINARY,  # or GRB.BINARY at the end
                obj=warehouse.openingCost,
                name=f"OpenWarehouse_{warehouse.warehouseId}"
            )

            # For each time period, create the capacity constraint
            for t in self.problem.timePeriods:
                cap_constr = self.model.addConstr(
                    LinExpr() <= 0.0,
                    name=f"WarehouseCapacity_{warehouse.warehouseId}_T{t}"
                )
                # sum_{x_r} weight - capacity*y_var <= 0
                # We only add the -capacity*y_var piece here;
                # the route variables x_r get added in addColumns(...).
                self.model.chgCoeff(cap_constr, y_var, -warehouse.capacity)

        self.model.update()

    def findWarehousePair(self, shipment, country, postalCode, startPoint, weight, dangerous, isPickUp):
        for warehouse in self.problem.warehouses:
            warehouseId = warehouse.warehouseId

            if warehouseId in ["WH1", "WH2"]:
                tildeCost = warehouse.shuttleCost * weight
            else:
                tildeCost = self.calculateCostBetweenPoints(warehouse.country, warehouse.postalCode, startPoint, weight, dangerous)
            if not isPickUp:
                if warehouseId in ["WH1", "WH2"]:
                    tildeCost += self.calculateCostBetweenPoints(country, postalCode, startPoint, weight, dangerous)
                else:
                    tildeCost += self.calculateCostBetweenPoints(country, postalCode, warehouseId, weight, dangerous)

            tildeCost += self.calculateWarehouseCost(warehouse, shipment)

            self.columns[shipment.month][shipment.shipmentId].append([tildeCost, warehouseId])

    def calculateCostBetweenPoints(self, country, postalCode, startPoint, weight, dangerous):
        CHList = ["CH00", "CH01", "CH02"]

        if startPoint in CHList:
            startPoint = self.searchCHStartingPoint(country, postalCode, startPoint)

        route_cost = self.problem.routeCostDictionary.calculateRouteCost(country, postalCode, startPoint, weight, dangerous)
        kilometers = self.problem.routeCostDictionary.getDistance(country, postalCode, startPoint)
        leadtime = self.problem.routeCostDictionary.getLeadtime(country, postalCode, startPoint)

        return self.problem.gamma * route_cost + (self.problem.alpha * self.problem.eta * weight * kilometers) + (self.problem.beta * leadtime)

    def searchCHStartingPoint(self, country, postal_code, startPoint):
        possible_primary = ["CH00", "CH01", "CH02"]
        possible_secondary = ["CH04", "CHS1"]
        routeCostDictionary = self.problem.routeCostDictionary.routeCostDictionary

        # Check if the given dep_shipping_point has "Minimum"
        try:
            if "Minimum" in routeCostDictionary[country][postal_code][startPoint]:
                return startPoint
        except KeyError:
            pass  # If key doesn't exist, continue checking other options

        # Store the best option (lowest cost and corresponding dep_shipping_point)
        min_cost = float("inf")
        best_point = None

        # Check among CH00, CH01, CH02
        for alt_point in possible_primary:
            try:
                cost = routeCostDictionary[country][postal_code][alt_point]["Minimum"]
                if cost < min_cost:
                    min_cost = cost
                    best_point = alt_point
            except KeyError:
                continue  # Skip if key doesn't exist

        if best_point:
            return best_point  # Return the best dep_shipping_point from the primary set

        # If no valid point found, check CH04, CHS1
        for alt_point in possible_secondary:
            try:
                cost = routeCostDictionary[country][postal_code][alt_point]["Minimum"]
                if cost < min_cost:
                    min_cost = cost
                    best_point = alt_point
            except KeyError:
                continue  # Skip if key doesn't exist

        return best_point  # Return the best dep_shipping_point found, or None if none exist

    def calculateWarehouseCost(self, warehouse, shipment):
        isDangerous = shipment.isDangerous
        cost = warehouse.inboundCost + warehouse.outboundCost

        multiplier = 1 # For MTO
        if shipment.planning == "MTO":
            multiplier = 0.25

        if isDangerous:
            cost += warehouse.dgCost * multiplier
        else:
            cost += warehouse.nonDgCost * multiplier
        cost = cost * shipment.weight

        return cost