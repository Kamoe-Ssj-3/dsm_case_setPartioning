import pandas as pd
import csv
import re

from shipment import Shipment
from production_site import ProductionSite
from warehouse import Warehouse


class Problem:
    def __init__(self, filepath, csvFilePath):
        self.shipments, self.sites, self.warehouses = self.extract_data(filepath)
        self.routeCostDictionary = self.build_cost_dictionary_from_csv(csvFilePath)

    @staticmethod
    def extract_data(file_path):
        df = pd.read_csv(file_path, delimiter=';')  # Use correct delimiter
        df.columns = df.columns.str.strip()

        shipments = []
        for _, row in df.iterrows():
            month = str(row["Month-Year"])[-2:]
            postalCode = str(row["Postal Code 2 digits"]).strip()[:2]
            country = row["Country of Destination"]

            if country.strip().lower() == "pickup":
                postalCode = "Null"
                country = "null"
                isPickUp = True
            else:
                isPickUp = False

            isDangerous = str(row["Dangerous Goods"]).strip().lower() == "dg"
            weight = row["KG2"]
            planning = row["Planning"]
            startingPoint = row["Starting Point"]

            shipment = Shipment(
                month=month,
                postalCode=postalCode,
                country=country,
                weight=weight,
                isPickUp=isPickUp,
                isDangerous=isDangerous,
                planning=planning,
                startingPoint=startingPoint,
            )
            shipments.append(shipment)

        numberOfSites = 3
        sites = []
        for i in range(numberOfSites):
            if i == 1:
                site = ProductionSite(
                    siteId=f'CH0{i}',
                    postalCode='12',
                    country='CH',
                    capacity=250000
                )
            else:
                site = ProductionSite(
                    siteId=f'CH0{i}',
                    postalCode='12',
                    country='CH',
                    capacity=0
                )

            sites.append(site)

        numberOfWarehouses = 6
        warehouses = []
        cr = 1.06
        for i in range(numberOfWarehouses):
            if i == 0:
                warehouse = Warehouse(
                    warehouseId='WH1',
                    postalCode='12',
                    country='CH',
                    capacity=1000 * 700,
                    shuttleCost=0.1,
                    xDockCost=0.1,
                    nonDgCost=None,
                    dgCost=None,
                    inboundCost=10 * cr / 700,
                    outboundCost=10 * cr / 700
                )
            elif i == 1:
                warehouse = Warehouse(
                    warehouseId='WH2',
                    postalCode='12',
                    country='CH',
                    capacity=2000 * 700,
                    shuttleCost=0.05,
                    xDockCost=None,
                    nonDgCost=15 * cr / 700,
                    dgCost=15 * cr / 700,
                    inboundCost=10 * cr / 700,
                    outboundCost=10 * cr / 700
                )
            else:
                warehouseId='' # Niet nodig?
                if i == 2:
                    warehouseId = 'FR01'
                elif i == 3:
                    warehouseId = 'ES50'
                elif i == 4:
                    warehouseId = 'PL46'
                else:
                    warehouseId = 'TR59'

                warehouse = Warehouse(
                    warehouseId=warehouseId,
                    postalCode='74',
                    country='FR',
                    capacity=5000 * 700,
                    shuttleCost=0.05,
                    xDockCost=None,
                    nonDgCost=8 / 700,
                    dgCost=12 / 700,
                    inboundCost=4 / 700,
                    outboundCost=4 / 700
                )
            warehouses.append(warehouse)

        return shipments, sites, warehouses

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
            #"Sample shipment (no minimum calculation)",
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