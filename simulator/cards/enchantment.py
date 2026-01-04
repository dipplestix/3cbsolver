"""Enchantment base class for the 3CB simulator."""
from typing import List, Dict, Optional, TYPE_CHECKING

from .base import Card, Action

if TYPE_CHECKING:
    from ..game_state import GameState


class Enchantment(Card):
    """Base class for enchantment cards."""

    def __init__(self, name: str, owner: int,
                 color_costs: Optional[Dict[str, int]] = None,
                 generic_cost: int = 0):
        """Initialize enchantment.

        Args:
            name: Card name
            owner: Player index (0 or 1)
            color_costs: Dict of colored mana required, e.g. {'W': 1} for {W},
                        {'W': 2} for {W}{W}, {'B': 1, 'G': 1} for {B}{G}
            generic_cost: Amount of generic mana required (can use any color)
        """
        super().__init__(name, owner)
        self.color_costs = color_costs or {}
        self.generic_cost = generic_cost

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        """Cast enchantment from hand."""
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        # Calculate total mana needed
        total_colored = sum(self.color_costs.values())
        total_needed = total_colored + self.generic_cost

        # Check total mana available
        if state.get_available_mana(self.owner) < total_needed:
            return []

        # Check each color requirement
        available = state.get_available_mana_by_color(self.owner)
        for color, amount in self.color_costs.items():
            if available.get(color, 0) < amount:
                return []

        # Capture costs for closure
        color_costs = self.color_costs.copy()
        generic_cost = self.generic_cost

        def cast(s: 'GameState') -> 'GameState':
            ns = s.copy()
            # Pay each colored cost
            for color, amount in color_costs.items():
                ns = ns.pay_mana(self.owner, color, amount)
            # Pay generic cost
            if generic_cost > 0:
                ns = ns.pay_generic_mana(self.owner, generic_cost)

            # Remove from hand and add to enchantments
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    enchantment = ns.hands[self.owner].pop(i)
                    ns.enchantments[self.owner].append(enchantment)
                    break

            return ns

        return [Action(f"Cast {self.name}", cast)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Enchantments typically don't have activated abilities."""
        return []

    def on_opponent_upkeep(self, state: 'GameState') -> 'GameState':
        """Called at the beginning of opponent's upkeep.

        Override in subclasses for enchantments that trigger on opponent's upkeep.
        """
        return state

    def is_creature(self) -> bool:
        return False

    def get_signature_state(self) -> tuple:
        """Return hashable state for memoization."""
        return (self.name, self.tapped)

    def copy(self) -> 'Enchantment':
        """Create a deep copy of this enchantment."""
        new_enchantment = Enchantment(
            self.name, self.owner,
            color_costs=self.color_costs.copy(),
            generic_cost=self.generic_cost
        )
        new_enchantment.tapped = self.tapped
        return new_enchantment
