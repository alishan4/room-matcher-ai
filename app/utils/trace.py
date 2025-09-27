from typing import List, Dict, Any

class Trace:
    def __init__(self, mode:str="degraded"):
        self.mode = mode
        self.steps: List[Dict[str,Any]] = []

    def add_step(self, agent:str, inputs:Dict[str,Any], outputs:Dict[str,Any]):
        self.steps.append({"agent": agent, "inputs": inputs, "outputs": outputs})

    def to_dict(self)->Dict[str,Any]:
        return {"mode": self.mode, "steps": self.steps}
