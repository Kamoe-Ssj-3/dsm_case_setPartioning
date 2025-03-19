import pprint
import time

from problem import Problem
from column_generation import ColumnGeneration
from exact_algorithm import ExactAlgorithm

from itertools import product

def main():
    filePath = "shipment_data_def.csv"
    csvFilePath = "RoadRate_with_all_lanes.csv"

    # problem = Problem(filePath, csvFilePath)

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

    start = time.time()

    problem = Problem(filePath, csvFilePath, 1, 0.1, 100)

    # value = ColumnGeneration(problem).run()

    exact = ExactAlgorithm(problem)
    exact.solve()
    exact.calculateSeparateCost()

    end = time.time()
    print("Total time: ", end-start)

    # gamma_values = [1, 2]
    # alpha_values = [0.1, 0.2]
    # beta_values = [100, 200]
    #
    # results_CG = []
    # results_Exact = []
    #
    # for scenario, (gamma, alpha, beta) in enumerate(product(gamma_values, alpha_values, beta_values), start=1):
    #     print(f"Running with gamma={gamma}, alpha={alpha}, beta={beta}")
    #
    #     problem = Problem(filePath, csvFilePath, gamma, alpha, beta)
    #
    #     valueCG, warehousesCG = ColumnGeneration(problem).run()
    #     results_CG.append((scenario, valueCG, [i + 1 for i, w in enumerate(warehousesCG) if w == 1.0]))
    #
    #     exact = ExactAlgorithm(problem)
    #     valueExact, warehousesExact = exact.solve()
    #     results_Exact.append((scenario, valueExact, [i + 1 for i, w in enumerate(warehousesExact) if w == 1.0]))
    #
    # # Generate Overleaf tables
    # def generate_table(results, method_name):
    #     table = """
    #     \begin{table}[h]
    #     \centering
    #     \begin{tabular}{lll}
    #     \textbf{Scenario} & \textbf{Objective Value} & \textbf{Open Warehouses} \\ \hline
    #     """
    #     for scenario, value, warehouses in results:
    #         warehouses_str = ", ".join(map(str, warehouses))
    #         table += f"Scenario {scenario} & {value:.2f} & {warehouses_str} \\ \n"
    #
    #     table += "\end{tabular}\n"
    #     table += f"\caption{{Objective values and warehouse selections for {method_name}}}\n"
    #     table += f"\label{{tab:{method_name.lower().replace(' ', '-')}-results}}\n"
    #     table += "\end{table}"
    #     return table
    #
    # cg_table = generate_table(results_CG, "Column Generation")
    # exact_table = generate_table(results_Exact, "Exact Algorithm")
    #
    # print(cg_table)
    # print(exact_table)


if __name__ == "__main__":
    main()