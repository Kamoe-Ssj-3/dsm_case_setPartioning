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

    def getCost(self, country, postal_code, startPoint, weight):
        """
        Retrieves the cost for a given weight by finding the smallest weight category that is greater than or equal to the given weight.
        """
        cost = 0

        if weight > 20000:
            cost = self.routeCostDictionary[country][postal_code][startPoint]["FTL"]
            weight -= 20000
        if postal_code == 'Ir':
            print(postal_code)
        minCost = self.routeCostDictionary[country][postal_code][startPoint]["Minimum"]
        for max_weight, cost_category in self.weight_categories:
            if weight <= max_weight:
                customClearance = self.routeCostDictionary[country][postal_code][startPoint]["Custom Clearance"]
                if cost_category != "FTL":
                    cost += self.routeCostDictionary[country][postal_code][startPoint][cost_category] / 100 * weight
                else:
                    cost += self.routeCostDictionary[country][postal_code][startPoint][cost_category]
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