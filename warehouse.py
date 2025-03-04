class Warehouse:
    def __init__(self, warehouseId, postalCode, country, capacity, openingCost, shuttleCost, nonDgCost, dgCost, inboundCost, outboundCost):
        self.warehouseId = warehouseId
        self.postalCode = postalCode
        self.country = country
        self.capacity = capacity
        self.openingCost = openingCost
        self.shuttleCost = shuttleCost
        self.nonDgCost = nonDgCost
        self.dgCost = dgCost
        self.inboundCost = inboundCost
        self.outboundCost = outboundCost
