"""Instant base class for the 3CB simulator."""
from abc import abstractmethod
from typing import List, Dict, Optional, TYPE_CHECKING

from .base import Card, Action

if TYPE_CHECKING:
    from ..game_state import GameState


class Instant(Card):
    """Base class for instant cards.

    Instants can be cast during the response phase to respond to spells on the stack.
    After resolution, they go to the graveyard.
    """

    def __init__(self, name: str, owner: int,
                 color_costs: Optional[Dict[str, int]] = None,
                 generic_cost: int = 0):
        """Initialize instant.

        Args:
            name: Card name
            owner: Player index (0 or 1)
            color_costs: Dict of colored mana required, e.g. {'U': 1} for {U}
            generic_cost: Amount of generic mana required
        """
        super().__init__(name, owner)
        self.color_costs = color_costs or {}
        self.generic_cost = generic_cost

    def can_pay_mana_cost(self, state: 'GameState') -> bool:
        """Check if we have enough mana to cast this instant."""
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
        """Pay the mana costs for this instant."""
        ns = state.copy()
        # Pay each colored cost
        for color, amount in self.color_costs.items():
            ns = ns.pay_mana(self.owner, color, amount)
        # Pay generic cost
        if self.generic_cost > 0:
            ns = ns.pay_generic_mana(self.owner, self.generic_cost)
        return ns

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        """Instants are not cast from get_play_actions during main phase.

        They use get_response_actions during the response phase.
        """
        return []

    @abstractmethod
    def get_response_actions(self, state: 'GameState') -> List[Action]:
        """Get actions available when responding to a spell on the stack.

        Override in subclasses to check for valid targets and return
        appropriate cast actions.
        """
        pass

    @abstractmethod
    def resolve(self, state: 'GameState') -> 'GameState':
        """Resolve this instant's effect.

        Override in subclasses to implement the specific effect.
        """
        pass

    def is_creature(self) -> bool:
        return False

    def get_signature_state(self) -> tuple:
        """Return hashable state for memoization."""
        return (self.name,)

    def copy(self) -> 'Instant':
        """Create a deep copy of this instant."""
        new_instant = self.__class__.__new__(self.__class__)
        new_instant.name = self.name
        new_instant.owner = self.owner
        new_instant.tapped = self.tapped
        new_instant.color_costs = self.color_costs.copy()
        new_instant.generic_cost = self.generic_cost
        return new_instant
