class Shipment:
    def __init__(self, shipmentId, month, postalCode, country, weight, isPickUp, isDangerous, planning, startingPoint):
        self.shipmentId = shipmentId
        self.month = month
        self.postalCode = postalCode
        self.country = country
        self.weight = weight
        self.isPickUp = isPickUp
        self.isDangerous = isDangerous
        self.planning = planning
        self.startingPoint = startingPoint
