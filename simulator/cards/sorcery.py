"""Sorcery base class for the 3CB simulator."""
from abc import abstractmethod
from typing import List, Dict, Optional, TYPE_CHECKING

from .base import Card, Action

if TYPE_CHECKING:
    from ..game_state import GameState


class Sorcery(Card):
    """Base class for sorcery cards.

    Sorceries can only be cast during your main phase when the stack is empty.
    After resolution, they go to the graveyard.
    """

    def __init__(self, name: str, owner: int,
                 color_costs: Optional[Dict[str, int]] = None,
                 generic_cost: int = 0):
        """Initialize sorcery.

        Args:
            name: Card name
            owner: Player index (0 or 1)
            color_costs: Dict of colored mana required, e.g. {'B': 1} for {B}
            generic_cost: Amount of generic mana required
        """
        super().__init__(name, owner)
        self.color_costs = color_costs or {}
        self.generic_cost = generic_cost

    def can_cast(self, state: 'GameState') -> bool:
        """Check if this sorcery can be cast."""
        if state.active_player != self.owner:
            return False
        if state.phase != "main1":
            return False
        # Sorceries require empty stack
        if state.stack:
            return False

        # Calculate total mana needed
        total_colored = sum(self.color_costs.values())
        total_needed = total_colored + self.generic_cost

        # Check total mana available
        if state.get_available_mana(self.owner) < total_needed:
            return False

        # Check each color requirement
        available = state.get_available_mana_by_color(self.owner)
        for color, amount in self.color_costs.items():
            if available.get(color, 0) < amount:
                return False

        return True

    def pay_costs(self, state: 'GameState') -> 'GameState':
        """Pay the mana costs for this sorcery."""
        ns = state.copy()
        # Pay each colored cost
        for color, amount in self.color_costs.items():
            ns = ns.pay_mana(self.owner, color, amount)
        # Pay generic cost
        if self.generic_cost > 0:
            ns = ns.pay_generic_mana(self.owner, self.generic_cost)
        return ns

    @abstractmethod
    def resolve(self, state: 'GameState') -> 'GameState':
        """Resolve this sorcery's effect.

        Override in subclasses to implement the specific effect.
        The sorcery is already removed from hand at this point.
        After this returns, the sorcery will be moved to graveyard.
        """
        pass

    def is_creature(self) -> bool:
        return False

    def get_signature_state(self) -> tuple:
        """Return hashable state for memoization."""
        return (self.name,)

    def copy(self) -> 'Sorcery':
        """Create a deep copy of this sorcery."""
        new_sorcery = self.__class__.__new__(self.__class__)
        new_sorcery.name = self.name
        new_sorcery.owner = self.owner
        new_sorcery.tapped = self.tapped
        new_sorcery.color_costs = self.color_costs.copy()
        new_sorcery.generic_cost = self.generic_cost
        return new_sorcery
