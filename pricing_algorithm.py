
class PricingAlgorithm:

    def __init__(self, problem):
        self.problem = problem

    def find(self, lambdas, mu, sigma):
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

                self.addWarehouseRedCost(shipment, country, postalCode, startPoint, weight, dangerous, month,
                                         lambda_value, sigma)
            else:
                self.addWarehouseRedCost(shipment, country, postalCode, startPoint, weight, dangerous, month,
                                         lambda_value, sigma)

    def addWarehouseRedCost(self, shipment, country, postalCode, startPoint, weight, dangerous, month, lambda_value,
                            sigma):
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
