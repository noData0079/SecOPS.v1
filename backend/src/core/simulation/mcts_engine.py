import math
import random
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MCTSEngine:
    """
    Monte Carlo Tree Search Engine for "What-If" simulations.
    """
    def __init__(self, simulation_budget: int = 1000):
        self.simulation_budget = simulation_budget

    def simulate_change(self, initial_state: Dict[str, Any], proposed_change: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs MCTS to predict the outcome of a proposed change.
        """
        root = MCTSNode(state=initial_state, change=proposed_change)

        for _ in range(self.simulation_budget):
            node = self._select(root)
            if not node.is_terminal():
                node = self._expand(node)
            outcome = self._simulate(node)
            self._backpropagate(node, outcome)

        best_child = root.best_child()
        if best_child:
            return {
                "recommended": True,
                "safety_score": best_child.win_rate(),
                "visits": best_child.visits
            }
        return {"recommended": False, "safety_score": 0.0}

    def _select(self, node: 'MCTSNode') -> 'MCTSNode':
        """
        Selects the best node to expand using UCB1.
        """
        while not node.is_leaf():
            if not node.is_fully_expanded():
                return node
            node = node.best_ucb_child()
        return node

    def _expand(self, node: 'MCTSNode') -> 'MCTSNode':
        """
        Expands the node by adding a child state.
        """
        # In a real scenario, this would generate a new state based on available actions.
        # Here we verify simple expansion.
        new_state = node.state.copy()
        # perturbations
        new_state['latency'] = new_state.get('latency', 10) + random.randint(-2, 5)

        child = MCTSNode(state=new_state, parent=node)
        node.children.append(child)
        return child

    def _simulate(self, node: 'MCTSNode') -> float:
        """
        Simulates a rollout from the node's state.
        Returns a score (0.0 to 1.0).
        """
        # Heuristic simulation
        latency = node.state.get('latency', 10)
        error_rate = node.state.get('error_rate', 0.0)

        if latency > 100 or error_rate > 0.01:
            return 0.0 # Failure
        return 1.0 # Success

    def _backpropagate(self, node: 'MCTSNode', outcome: float):
        """
        Updates the node and its ancestors with the simulation outcome.
        """
        while node:
            node.visits += 1
            node.value += outcome
            node = node.parent

class MCTSNode:
    def __init__(self, state: Dict[str, Any], parent: Optional['MCTSNode'] = None, change: Optional[Dict[str, Any]] = None):
        self.state = state
        self.parent = parent
        self.change = change
        self.children = []
        self.visits = 0
        self.value = 0.0

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def is_terminal(self) -> bool:
        # Simplified terminal condition
        return self.state.get('latency', 0) > 200

    def is_fully_expanded(self) -> bool:
        # Simplified: limit branching factor
        return len(self.children) >= 3

    def win_rate(self) -> float:
        return self.value / self.visits if self.visits > 0 else 0.0

    def best_child(self) -> Optional['MCTSNode']:
        if not self.children:
            return None
        return max(self.children, key=lambda c: c.visits)

    def best_ucb_child(self, c_param: float = 1.41) -> 'MCTSNode':
        # Upper Confidence Bound 1
        return max(self.children, key=lambda c: (c.value / c.visits) + c_param * math.sqrt(math.log(self.visits) / c.visits))
