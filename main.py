import pprint

from problem import Problem

def main():
    filePath = "shipment_data.csv"
    csvFilePath = "road_cost.csv"

    problem = Problem(filePath, csvFilePath)

    print("Shipments:")
    for s in problem.shipments[:50]:
        print(s.month, s.postalCode, s.country, s.isDangerous, s.weight, s.isDelivery)

    print()
    print("Sites:")
    for s in problem.sites:
        print(s.siteId, s.postalCode, s.country, s.capacity)

    print()
    print("Warehouses:")
    for w in problem.warehouses:
        print(w.warehouseId, w.postalCode, w.country, w.capacity, w.shuttleCost,
              w.xDockCost, w.nonDgCost, w.dgCost, w.inboundCost, w.outboundCost)

    print()
    print('Cost dictionary:')
    pprint.pprint(problem.routeCostDictionary)


if __name__ == "__main__":
    main()