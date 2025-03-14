from spp_model import SPPModel
from pricing_algorithm import PricingAlgorithm

class ColumnGeneration:
    def __init__(self, problem):
        self.problem = problem

    def run(self):
        # Instantiate the master problem (RMP)
        model = SPPModel(self.problem)
        model.initialize_RMP()

        pricingAlg = PricingAlgorithm(self.problem)

        iteration = 0
        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # Solve the restricted master problem
            lambdas, mu, sigma, objValue = model.solveRMP()
            print(f"Current objective value: {objValue}")

            columns, overgebleven = pricingAlg.find(lambdas, mu, sigma)

            if not columns:
                break

            model.addColumns(columns)

        # model.printConstraints()

        print("Final objective value Relaxation:", objValue)

        model.convertAllVarsToBinary()

        finalObjVal = model.solve()

        print("Final objective value:", finalObjVal)

        print("Number of columns added: ", pricingAlg.numberOfColumns)

        return finalObjVal