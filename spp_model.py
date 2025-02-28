from gurobipy import Model, GRB, quicksum

class SPPModel:
    def __init__(self, problem):
        self.problem = problem
        self.model = None

    def initialize_RMP(self, bigM=1e5):
        self.model = Model("SPP")

        for idx, shipment in enumerate(self.problem.shipments):
            slack_var = self.model.addVar(
                lb=0,
                vtype=GRB.CONTINUOUS,
                obj=bigM,
                name=f"Slack_{idx}"
            )
            self.model.addConstr(slack_var == 1, name=f"CoverShipment_{idx}")

        for site in self.problem.sites:
            for t in self.problem.timePeriods:
                self.model.addConstr(
                    0 <= site.capacity,
                    name=f"ProductionCapacity_{site.siteId}_T{t}"
                )

        for warehouse in self.problem.warehouses:
            y_var = self.model.addVar(
                vtype=GRB.CONTINUOUS,
                obj=warehouse.openingCost,
                name=f"OpenWarehouse_{warehouse.warehouseId}"
            )

            for t in self.problem.timePeriods:
                self.model.addConstr(
                    0 <= warehouse.capacity * y_var,
                    name=f"WarehouseCapacity_{warehouse.warehouseId}_T{t}"
                )

        self.model.update()

    def solveRMP(self):
        self.model.optimize()
        return self.model.ObjVal



    # def addColumns(self, pairs):


