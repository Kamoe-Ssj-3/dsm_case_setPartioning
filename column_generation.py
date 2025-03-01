from spp_model import SPPModel

class ColumnGeneration:
    def __init__(self, problem):
        self.problem = problem

    def run(self):
        model = SPPModel(self.problem)

        model.initialize_RMP()

        lambdas, mu, sigma = model.solveRMP()
        print(lambdas)







