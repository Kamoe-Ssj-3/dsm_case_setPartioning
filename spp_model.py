from gurobipy import Model, GRB, quicksum, LinExpr

class SPPModel:
    def __init__(self, problem):
        self.problem = problem
        self.model = None
        self.routeCostDict = self.problem.routeCostDictionary
        self.reducedCostList = []

    def initialize_RMP(self, bigM=1e7):
        self.model = Model("SPP")


        for shipment in self.problem.shipments:
            slack_var = self.model.addVar(
                lb=0,
                vtype=GRB.CONTINUOUS,
                obj=bigM,
                name=f"Slack_{shipment.shipmentId}"
            )
            self.model.addConstr(slack_var == 1, name=f"CoverShipment_{shipment.shipmentId}")

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
                vtype=GRB.CONTINUOUS,  # or GRB.BINARY at the end
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

    def solveRMP(self):
        self.model.setParam('OutputFlag', 0)
        self.model.optimize()

        if self.model.status != GRB.OPTIMAL:
            return None, None, None

        lambdas = []
        for idx in range(len(self.problem.shipments)):
            c = self.model.getConstrByName(f"CoverShipment_{idx}")
            lambdas.append(c.Pi)

        mu = []
        for t in self.problem.timePeriods:
            c_name = f"ProductionCapacity_CH01_T{t}"
            c = self.model.getConstrByName(c_name)
            mu.append(c.Pi)

        sigma = {} # Key: (warehouseId, timePeriod), Value: dual value
        for warehouse in self.problem.warehouses:
            for t in self.problem.timePeriods:
                c_name = f"WarehouseCapacity_{warehouse.warehouseId}_T{t}"
                c = self.model.getConstrByName(c_name)
                sigma[(warehouse.warehouseId, t)] = c.Pi

        return lambdas, mu, sigma, self.model.ObjVal

    def addColumns(self, columns):
        for col in columns:
            route_obj = col[0]  # objective contribution
            route_wh = col[1]  # warehouse or production site
            shipment = col[2]  # shipment object

            # Create a new variable for this route in the RMP:
            var_name = f"Route_Sh{shipment.shipmentId}_via_{route_wh}"
            route_var = self.model.addVar(
                lb=0,
                ub=1,
                obj=route_obj,
                vtype=GRB.CONTINUOUS,
                name=var_name
            )
            # 1. Add to "cover shipment" constraint:
            cover_constr = self.model.getConstrByName(f"CoverShipment_{shipment.shipmentId}")
            # Coefficient = 1 if this route covers that shipment
            self.model.chgCoeff(cover_constr, route_var, 1.0)

            # 2. Add capacity usage to the correct constraint(s):
            #    We'll assume shipment has some .timePeriod or similar attribute
            #    and that route_wh can be a production site or a warehouse.
            t = shipment.month
            w_s = shipment.weight

            # If route_wh is a production site (e.g. "CH01"), update the production constraint
            if route_wh == 'CH01':  # or however you identify it
                constr_name = f"ProductionCapacity_CH01_T{t}"
                cap_constr = self.model.getConstrByName(constr_name)
                self.model.chgCoeff(cap_constr, route_var, w_s)
            else:
                # Otherwise, this must be a warehouse
                constr_name = f"WarehouseCapacity_{route_wh}_T{t}"
                cap_constr = self.model.getConstrByName(constr_name)
                self.model.chgCoeff(cap_constr, route_var, w_s)

        # After adding all the route columns, update the model
        self.model.update()

    def convertAllVarsToBinary(self):
        for var in self.model.getVars():
            var.VType = GRB.BINARY

        self.model.update()

    def solve(self):
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

    def printConstraints(self):
        """
        Print each constraint in a human-readable form, e.g.:
        CoverShipment_123: 1.0*Slack_123 + 2.0*Route_Sh123_via_WH1 <= 10
        """
        for constr in self.model.getConstrs():
            lhs_expr = self.model.getRow(constr)  # A gurobipy.LinExpr
            sense = constr.Sense
            rhs = constr.RHS
            name = constr.ConstrName

            # Convert Gurobi's sense character to a more standard operator
            if sense == '>':
                sense_str = '>='
            elif sense == '<':
                sense_str = '<='
            else:
                sense_str = '=='  # '=' case

            # Build a string like "2.0*X1 + 1.0*X2"
            terms = []
            for i in range(lhs_expr.size()):
                coeff = lhs_expr.getCoeff(i)
                var = lhs_expr.getVar(i)
                terms.append(f"{coeff}*{var.VarName}")

            lhs_str = " + ".join(terms)

            print(f"{name}: {lhs_str} {sense_str} {rhs}")
