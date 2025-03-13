import pprint

from problem import Problem
from column_generation import ColumnGeneration
from exact_algorithm import ExactAlgorithm

def main():
    filePath = "shipment_data_def.csv"
    csvFilePath = "RoadRate_with_all_lanes.csv"

    problem = Problem(filePath, csvFilePath)

    # print("Shipments:")
    # for s in problem.shipments:
    #     print(s.shipmentId, s.month, s.postalCode, s.country, s.isDangerous, s.weight, s.isPickUp, s.planning, s.startingPoint)
    #
    # print()
    # print("Sites:")
    # for s in problem.sites:
    #     print(s.siteId, s.postalCode, s.country, s.capacity)
    #
    # print()
    # print("Warehouses:")
    # for w in problem.warehouses:
    #     print(w.warehouseId, w.postalCode, w.country, w.capacity, w.shuttleCost, w.nonDgCost, w.dgCost, w.inboundCost, w.outboundCost)

    print()
    # print('Cost dictionary:')
    # pprint.pprint(problem.routeCostDictionary)

    value = ColumnGeneration(problem).run()

    # exact = ExactAlgorithm(problem)
    # exact.solve()

if __name__ == "__main__":
    main()