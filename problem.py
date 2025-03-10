import pandas as pd
import csv
import re

from route_cost import RouteCost
from shipment import Shipment
from production_site import ProductionSite
from warehouse import Warehouse


class Problem:
    def __init__(self, filepath, csvFilePath):
        self.shipments, self.sites, self.warehouses = self.extract_data(filepath)
        self.timePeriods = list(range(1, 13))
        self.routeCostDictionary = RouteCost(csvFilePath)
        self.gamma = 1
        self.alpha = 0.1
        self.eta = 0.129
        self.beta = 100

    @staticmethod
    def extract_data(file_path):
        df = pd.read_csv(file_path, delimiter=';')
        df.columns = df.columns.str.strip()

        shipments = []
        for idx, row in df.iterrows():
            if idx > 150000:
                break

            month = int(str(row["Month-Year"])[-2:])
            postalCode = str(row["Postal Code 2 digits"])
            country = row["Country of Destination"]

            if country.strip().lower() == "pickup":
                postalCode = "Null"
                country = "Null"
                isPickUp = True
            else:
                isPickUp = False

            isDangerous = str(row["Dangerous Goods"]).strip().lower() == "dg"
            weight = row["KG2"]
            planning = row["Planning"]
            startingPoint = row["Starting Point"]

            shipment = Shipment(
                shipmentId=idx,
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
                    openingCost=1e-6,
                    shuttleCost=0.1 * cr,
                    nonDgCost=0,
                    dgCost=0,
                    inboundCost=10 * cr / 700,
                    outboundCost=10 * cr / 700
                )
            elif i == 1:
                warehouse = Warehouse(
                    warehouseId='WH2',
                    postalCode='12',
                    country='CH',
                    capacity=2000 * 700,
                    openingCost=1e-6,
                    shuttleCost=0.05 * cr,
                    nonDgCost=15 * cr / 700,
                    dgCost=15 * cr / 700,
                    inboundCost=10 * cr / 700,
                    outboundCost=10 * cr / 700
                )
            else:
                if i == 2:
                    warehouseId = 'FR01'
                    country = 'FR'
                    postalCode = '74'
                    openingCost = 1e-6
                elif i == 3:
                    warehouseId = 'ES50'
                    country = 'ES'
                    postalCode = '50'
                    openingCost = 500000
                elif i == 4:
                    warehouseId = 'PL46'
                    country = 'PL'
                    postalCode = '46'
                    openingCost = 500000
                else:
                    warehouseId = 'TR59'
                    country = 'TR'
                    postalCode = '59'
                    openingCost = 500000

                warehouse = Warehouse(
                    warehouseId=warehouseId,
                    postalCode=postalCode,
                    country=country,
                    capacity=5000 * 700,
                    openingCost=openingCost,
                    shuttleCost=0,
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

