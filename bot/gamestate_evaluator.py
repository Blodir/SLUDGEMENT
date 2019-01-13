class GamestateEvaluator():
    def __init__(self):
        self.scouting_confidence: float = 1
    
    def iterate(self):
        self.scouting_confidence -= 0.01
    