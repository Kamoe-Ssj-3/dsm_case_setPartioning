import csv
import re

class RouteCost:
    def __init__(self, csvFilePath):
        self.routeCostDictionary = self.build_cost_dictionary_from_csv(csvFilePath)

    def extract_numeric_value(self, value):
        """
        Extracts the first numeric value from a string and converts it to a float.
        If no numeric value is found, returns None.
        """
        match = re.search(r"[\d,]+(?:\.\d+)?", value)  # Match numbers, including decimals
        if match:
            return float(match.group().replace(",", ""))  # Convert to float, remove thousands separator
        return None  # Return None if no number is found


    def build_cost_dictionary_from_csv(self, csv_file_path):
        """
        Reads the CSV file and builds a nested dictionary of the form:
        {
          country_code: {
             postal_2digits: {
                dep_shipping_point: {
                   'Minimum': float,
                   '<=50kg': float,
                   '<=100kg': float,
                   ...
                   'DG Surcharge per shipment': float
                }
             }
          }
        }
        """
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
            "Sample shipment (no minimum calculation)",
            "Custom Clearance",
            "DG Surcharge per shipment"
        ]

        result = {}

        with open(csv_file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                dep_shipping_point = row["Dep.shipping point"].strip()
                ship_to_country = row["Ship to Country code"].strip()
                postal_2digits = row["Ship to simplified postcode 2 digits"].strip()

                if ship_to_country not in result:
                    result[ship_to_country] = {}

                if postal_2digits not in result[ship_to_country]:
                    result[ship_to_country][postal_2digits] = {}

                cost_dict = {key: self.extract_numeric_value(row[key]) for key in cost_keys}

                result[ship_to_country][postal_2digits][dep_shipping_point] = cost_dict

        return result


# # --------------------------
# # Example usage:
# # --------------------------
# if __name__ == "__main__":
#     csv_path = "road_cost.csv"  # Replace with your actual CSV file path
#     nested_dict = build_cost_dictionary_from_csv(csv_path)
#
#     # Print or inspect the resulting nested dictionary
#     import pprint
#
#     pprint.pprint(nested_dict)
