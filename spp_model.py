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

        self.model.update()

    def solve(self):
        self.model.optimize()
        return self.model.ObjVal