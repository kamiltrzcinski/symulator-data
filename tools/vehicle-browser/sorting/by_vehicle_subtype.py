from models.vehicle_type import VehicleType


class SortByVehicleSubtype:
    label = "vehicleSubtype"

    def key(self, item: VehicleType):
        return (item.vehicleSubtype.lower(), item.vehicleType.lower(), item.typeName.lower())
