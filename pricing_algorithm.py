class PricingAlgorithm:

    def __init__(self, problem):
        self.problem = problem
        self.columns = []


    def find(self, lambdas, mu, sigma):
        self.columns = []

        sortedShipments = self.sortShipments(lambdas)

        for lambda_value, shipment in sortedShipments:
            country = shipment.country
            postalCode = shipment.postalCode
            startPoint = shipment.startingPoint
            weight = shipment.weight
            dangerous = shipment.isDangerous
            month = shipment.month
            isPickUp = shipment.isPickUp

            if startPoint == "CH01":
                if isPickUp:
                    tildeCost = 0
                else:
                    tildeCost = self.calculateCostBetweenPoints(country, postalCode, startPoint, weight, dangerous)
                self.findDirectPair(tildeCost, lambda_value, shipment, mu[month], startPoint)

                self.findWarehousePair(shipment, country, postalCode, startPoint, weight, dangerous, month,
                                       lambda_value, sigma, isPickUp)
            else:
                self.findWarehousePair(shipment, country, postalCode, startPoint, weight, dangerous, month,
                                       lambda_value, sigma, isPickUp)
        return self.columns

    def findWarehousePair(self, shipment, country, postalCode, startPoint, weight, dangerous, month, lambda_value,
                          sigma, isPickUp):
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

            self.findDirectPair(tildeCost, lambda_value, shipment, sigma[warehouseId, month], warehouseId)

    def findDirectPair(self, tildeCost, lambda_value, shipment, dual, pairPoint):
        reducedCost = self.calculateRedCost(tildeCost, lambda_value, shipment, dual)
        if reducedCost < 0:
            self.columns.append([tildeCost, pairPoint, shipment])

    def sortShipments(self, lambdas):
        sorted_lambdas = sorted(enumerate(lambdas), key=lambda x: x[1], reverse=True)
        # print("lambdas, gesorteerde volgorde")
        # print(sorted_lambdas[:1000])
        # # In 2e iteratie argmax lamda opslaan, dan self.problem.shipments[argmax] printen, en kijken of pairing goed gaat.
        # print("shipments, originele volgorde")
        # print(self.problem.shipments[:1000])
        sorted_data = [(value, self.problem.shipments[index]) for index, value in sorted_lambdas]
        # print("lambdas en shipments pairs, gesorteerde volgorde")
        # print(sorted_data[:1000])
        return sorted_data

    def calculateCostBetweenPoints(self, country, postalCode, startPoint, weight, dangerous):
        CHList = ["CH00", "CH01", "CH02"]

        if startPoint in CHList:
            startPoint = self.searchCHStartingPoint(country, postalCode, startPoint)

        route_cost = self.problem.routeCostDictionary.calculateRouteCost(country, postalCode, startPoint, weight, dangerous)
        kilometers = self.problem.routeCostDictionary.getDistance(country, postalCode, startPoint)
        leadtime = self.problem.routeCostDictionary.getLeadtime(country, postalCode, startPoint)

        return route_cost + (self.problem.alpha * self.problem.eta * kilometers) + (self.problem.beta * leadtime)

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

    def calculateRedCost(self, tildeCost, lambdaValue, shipment, secondDual):
        return tildeCost - lambdaValue - shipment.weight * secondDual

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
