from spp_model import SPPModel
from pricing_algorithm import PricingAlgorithm

class ColumnGeneration:
    def __init__(self, problem):
        self.problem = problem

    def run(self):
        model = SPPModel(self.problem)

        model.initialize_RMP()

        lambdas, mu, sigma = model.solveRMP()
        # print("Lambdas, originele volgorde")
        # print(lambdas[:1000])

        columns = PricingAlgorithm(self.problem).find(lambdas, mu, sigma)

        print(columns)


        #model.addColumns(columns)









