from sc2.unit import Unit

class UnitObservation():
    def __init__(self, unit: Unit, time_to_live: int):
        self.unit = unit
        self.time_to_live = time_to_live
    
    def iterate(self):
        self.time_to_live = self.time_to_live - 1
        if self.time_to_live == 0:
            return False
        return True

    def update_ttl(self, time_to_live: int):
        self.time_to_live = time_to_live