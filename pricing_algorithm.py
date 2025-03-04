class PricingAlgorithm:

    def __init__(self, problem):
        self.problem = problem
        self.columns = []


    def find(self, lambdas, mu, sigma):
        self.columns = []

        sortedShipments = self.sortShipments(lambdas)
        sortedShipments = sortedShipments[94:]

        for lambda_value, shipment in sortedShipments:
            country = shipment.country
            postalCode = shipment.postalCode
            startPoint = shipment.startingPoint
            weight = shipment.weight
            dangerous = shipment.isDangerous
            month = shipment.month

            # if country == "null":
            #     for warehouse in self.problem.warehouses:
            #         j
            # else:
            if startPoint == "CH01":
                tildeCost = self.calculateTildeCost(country, postalCode, startPoint, weight, dangerous)
                self.findDirectPair(tildeCost, lambda_value, shipment, mu[month], startPoint)

                self.findWarehousePair(shipment, country, postalCode, startPoint, weight, dangerous, month,
                                       lambda_value, sigma)
            else:
                self.findWarehousePair(shipment, country, postalCode, startPoint, weight, dangerous, month,
                                       lambda_value, sigma)
        return self.columns

    def findWarehousePair(self, shipment, country, postalCode, startPoint, weight, dangerous, month, lambda_value,
                          sigma):
        for warehouse in self.problem.warehouses:
            warehouseId = warehouse.warehouseId

            if warehouseId == ("WH1" or "WH2"):
                tildeCost = self.calculateTildeCost(warehouse.country, warehouse.postalCode, startPoint, weight,
                                                    dangerous)
                tildeCost += self.calculateTildeCost(country, postalCode, startPoint, weight, dangerous)

            tildeCost = self.calculateTildeCost(warehouse.country, warehouse.postalCode, startPoint, weight, dangerous)
            tildeCost += self.calculateTildeCost(country, postalCode, warehouseId, weight, dangerous)

            self.findDirectPair(tildeCost, lambda_value, shipment, sigma[warehouseId, month], warehouseId)

    def findDirectPair(self, tildeCost, lambda_value, shipment, dual, startPoint):
        reducedCost = self.calculateRedCost(tildeCost, lambda_value, shipment, dual)
        if reducedCost < 0:
            self.columns.append([tildeCost, startPoint, shipment])

    def sortShipments(self, lambdas):
        sorted_lambdas = sorted(enumerate(lambdas), key=lambda x: x[1], reverse=True)
        print("lambdas, gesorteerde volgorde")
        print(sorted_lambdas[:1000])
        # In 2e iteratie argmax lamda opslaan, dan self.problem.shipments[argmax] printen, en kijken of pairing goed gaat.
        print("shipments, originele volgorde")
        print(self.problem.shipments[:1000])
        sorted_data = [(value, self.problem.shipments[index]) for index, value in sorted_lambdas]
        print("lambdas en shipments pairs, gesorteerde volgorde")
        print(sorted_data[:1000])
        return sorted_data

    def calculateTildeCost(self, country, postalCode, startPoint, weight, dangerous):
        route_cost = self.problem.routeCostDictionary.calculateRouteCost(country, postalCode, startPoint, weight, dangerous)
        kilometers = self.problem.routeCostDictionary.getDistance(country, postalCode, startPoint)
        leadtime = self.problem.routeCostDictionary.getLeadtime(country, postalCode, startPoint)

        return route_cost + (self.problem.alpha * self.problem.eta * kilometers) + (self.problem.beta * leadtime)

    def calculateRedCost(self, tildeCost, lambdaValue, shipment, secondDual):
        return tildeCost - lambdaValue - shipment.weight * secondDual
