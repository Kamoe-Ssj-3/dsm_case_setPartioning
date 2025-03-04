import csv
import re

class RouteCost:
    def __init__(self, csvFilePath):
        self.routeCostDictionary = self.build_cost_dictionary_from_csv(csvFilePath)
        self.weight_categories = [
            (50, "<=50kg"),
            (100, "<=100kg"),
            (200, "<=200"),
            (400, "<=400"),
            (800, "<=800"),
            (1500, "<=1500"),
            (5000, "<=5000"),
            (10000, "<=10000"),
            (15000, "<=15000"),
            (20000, "FTL")
        ]

    def extract_numeric_value(self, value):
        match = re.search(r"[\d,]+(?:\.\d+)?", value)
        if match:
            return float(match.group().replace(",", ""))
        return None

    def build_cost_dictionary_from_csv(self, csv_file_path):
        cost_keys = [
            "Minimum",
            "<=50kg",
            "<=100kg",
            "<=200",
            "<=400",
            "<=800",
            "<=1500",
            "<=5000",
            "<=10000",
            "<=15000",
            "FTL",
            "Carrier Leadtime in working days",
            # "Sample shipment (no minimum calculation)",
            "Custom Clearance",
            "DG Surcharge per shipment",
            "Distance"
        ]

        result = {}

        with open(csv_file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")

            for row in reader:
                dep_shipping_point = row["Origin"].strip()
                ship_to_country = row["Ship to Country code"].strip()
                postal_2digits = row["Ship to simplified postcode 2 digits"].strip()

                if ship_to_country not in result:
                    result[ship_to_country] = {}

                if postal_2digits not in result[ship_to_country]:
                    result[ship_to_country][postal_2digits] = {}

                cost_dict = {key: self.extract_numeric_value(row[key]) for key in cost_keys}

                result[ship_to_country][postal_2digits][dep_shipping_point] = cost_dict

        return result

    def searchCHStartingPoint(self, country, postal_code, startPoint):
        possible_primary = ["CH00", "CH01", "CH02"]
        possible_secondary = ["CH04", "CHS1"]

        # Check if the given dep_shipping_point has "Minimum"
        try:
            if "Minimum" in self.routeCostDictionary[country][postal_code][startPoint]:
                return startPoint
        except KeyError:
            pass  # If key doesn't exist, continue checking other options

        # Store the best option (lowest cost and corresponding dep_shipping_point)
        min_cost = float("inf")
        best_point = None

        # Check among CH00, CH01, CH02
        for alt_point in possible_primary:
            try:
                cost = self.routeCostDictionary[country][postal_code][alt_point]["Minimum"]
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
                cost = self.routeCostDictionary[country][postal_code][alt_point]["Minimum"]
                if cost < min_cost:
                    min_cost = cost
                    best_point = alt_point
            except KeyError:
                continue  # Skip if key doesn't exist

        return best_point  # Return the best dep_shipping_point found, or None if none exist

    def getCost(self, country, postal_code, startPoint, weight):
        """
        Retrieves the cost for a given weight by finding the smallest weight category that is greater than or equal to the given weight.
        """
        cost = 0
        CHList = ["CH00", "CH01", "CH02"]

        if startPoint in CHList:
            startPoint = self.searchCHStartingPoint(country, postal_code, startPoint)

        if weight > 20000:
            cost = self.routeCostDictionary[country][postal_code][startPoint]["FTL"]
            weight -= 20000

        minCost = self.routeCostDictionary[country][postal_code][startPoint]["Minimum"]
        for max_weight, cost_category in self.weight_categories:
            if weight <= max_weight:
                customClearance = self.routeCostDictionary[country][postal_code][startPoint]["Custom Clearance"]
                cost += self.routeCostDictionary[country][postal_code][startPoint][cost_category] / 100 * weight
                cost += customClearance
                if cost < minCost:
                    return minCost
                else:
                    return cost

    def calculateRouteCost(self, country, postalCode, depPoint, weight, dangerous):
        route_cost = self.getCost(country, postalCode, depPoint, weight)
        if (dangerous):
            route_cost += self.getDGSurcharge(country, postalCode, depPoint)
        return route_cost

    def getDistance(self, country, postal_code, dep_point):
        return self.routeCostDictionary[country][postal_code][dep_point]["Distance"]

    def getLeadtime(self, country, postal_code, dep_point):
        return self.routeCostDictionary[country][postal_code][dep_point]["Carrier Leadtime in working days"]

    def getDGSurcharge(self, country, postal_code, dep_point):
        return self.routeCostDictionary[country][postal_code][dep_point]["DG Surcharge per shipment"]