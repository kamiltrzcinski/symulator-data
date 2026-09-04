import sys
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from find_path import BaseTractionStrategy, ElectricTractionStrategy

def test_base_traction_strategy_cost():
    strategy = BaseTractionStrategy()
    # 120 km/h for 10 km (10000 m) = 5 minutes
    cost = strategy.get_cost(10000, 120.0, "1", "C3", None)
    assert abs(cost - 5.0) < 0.01

def test_base_traction_strategy_line_change_penalty():
    strategy = BaseTractionStrategy()
    # Line change penalty adds 5.0 minutes
    cost = strategy.get_cost(10000, 120.0, "2", "C3", "1")
    assert abs(cost - 10.0) < 0.01

def test_electric_traction_strategy_forbidden():
    strategy = ElectricTractionStrategy()
    # Speed < 60 and class not in allowed list -> infinite cost
    cost = strategy.get_cost(10000, 40.0, "999", "B2", None)
    assert cost == float('inf')

def test_electric_traction_strategy_allowed():
    strategy = ElectricTractionStrategy()
    # Speed >= 60 -> allowed
    cost = strategy.get_cost(10000, 120.0, "1", "C3", None)
    assert abs(cost - 5.0) < 0.01

if __name__ == "__main__":
    test_base_traction_strategy_cost()
    test_base_traction_strategy_line_change_penalty()
    test_electric_traction_strategy_forbidden()
    test_electric_traction_strategy_allowed()
    print("All tests passed!")
