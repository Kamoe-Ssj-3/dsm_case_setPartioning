from gurobipy import Model, GRB, quicksum

class SPPModel:
    def __init__(self, problem):
        self.problem = problem
        self.model = None
        self.routeCostDict = self.problem.routeCostDictionary
        self.reducedCostList = []

    def initialize_RMP(self, bigM=1e5):
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
            self.model.addConstr(
                0 <= 250000,
                name=f"ProductionCapacity_{'CH01'}_T{t}"
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

        return lambdas, mu, sigma

    def pricingAlgorithm(self):
        self.reducedCostList = []
        lambdas, mu, sigma = self.solveRMP()

        sortedShipments = self.sortShipments(lambdas)

        for lambda_value, shipment in sortedShipments:
            country = shipment.country
            postalCode = shipment.postalCode
            startPoint = shipment.startingPoint
            weight = shipment.weight
            dangerous = shipment.is_dangerous
            month = shipment.month

            if startPoint == "CH01":
                tildeCost = self.calculateTildeCost(country, postalCode, startPoint, weight, dangerous)
                self.findColummns(tildeCost, lambda_value, shipment, mu[month], startPoint)

                self.addWarehouseRedCost(shipment, country, postalCode, startPoint, weight, dangerous, month, lambda_value, sigma)
            else:
                self.addWarehouseRedCost(shipment, country, postalCode, startPoint, weight, dangerous, month, lambda_value, sigma)

    def addWarehouseRedCost(self, shipment, country, postalCode, startPoint, weight, dangerous, month, lambda_value, sigma):
        for warehouse in self.problem.warehouses:
            warehouseId = warehouse.warehouseId

            tildeCost = self.calculateTildeCost(warehouse.country, warehouse.postalCode, startPoint, weight, dangerous)
            tildeCost += self.calculateTildeCost(country, postalCode, warehouseId, weight, dangerous)

            self.findColummns(tildeCost, lambda_value, shipment, sigma[warehouseId, month], warehouseId)

    def findColummns(self, tildeCost, lambda_value, shipment, dual, startPoint):
        reducedCost = self.calculateRedCost(tildeCost, lambda_value, shipment, dual)
        if reducedCost < 0:
            self.reducedCostList.append([reducedCost, startPoint, shipment])

    def sortShipments(self, lambdas):
        sorted_lambdas = sorted(enumerate(lambdas), key=lambda x: x[1], reverse=True)
        sorted_data = [(value, index, self.problem.shipments[index]) for index, value in sorted_lambdas]
        return sorted_data

    def calculateTildeCost(self, country, postalCode, startPoint, weight, dangerous):
        route_cost = self.routeCostDict.calculateRouteCost(country, postalCode, startPoint, weight, dangerous)
        kilometers = self.problem.routeCostDictionary.getDistance(country, postalCode, startPoint)
        leadtime = self.problem.routeCostDictionary.getLeadtime(country, postalCode, startPoint)

        return route_cost + (alpha * eta * kilometers) + (beta * leadtime)

    def calculateRedCost(self, tildeCost, lambdaValue, shipment, secondDual):
        return tildeCost - lambdaValue - shipment.weight * secondDual
