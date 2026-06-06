from models.vehicle_type import VehicleType


class SortByVehicleType:
    label = "vehicleType"

    def key(self, item: VehicleType):
        return (item.vehicleType.lower(), item.typeName.lower())
