class Shipment:
    def __init__(self, month, postalCode, country, weight, isDelivery, isDangerous):
        self.month = month
        self.postalCode = postalCode
        self.country = country
        self.isDangerous = isDangerous
        self.weight = weight
        self.isDelivery = isDelivery
