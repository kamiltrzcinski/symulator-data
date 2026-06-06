from models.vehicle_type import VehicleType


class SortByTypeName:
    label = "typeName"

    def key(self, item: VehicleType):
        return item.typeName.lower()
