"""Base card classes for the 3CB simulator."""
from dataclasses import dataclass
from typing import List, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod
from enum import Enum, auto

if TYPE_CHECKING:
    from ..solver import GameState


class CardType(Enum):
    LAND = auto()
    CREATURE = auto()
    ARTIFACT = auto()
    ENCHANTMENT = auto()
    INSTANT = auto()
    SORCERY = auto()


@dataclass
class Action:
    """Represents an action that can be taken."""
    description: str
    execute: Callable[['GameState'], 'GameState']

    def __str__(self):
        return self.description


class Card(ABC):
    """Base class for all cards."""

    def __init__(self, name: str, owner: int):
        self.name = name
        self.owner = owner
        self.tapped = False

    def __repr__(self):
        tap_str = " (T)" if self.tapped else ""
        return f"{self.name}{tap_str}"

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        """Actions available when this card is in hand."""
        return []

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Actions available when this card is on the battlefield."""
        return []

    def get_attack_actions(self, state: 'GameState') -> List[Action]:
        """Attack actions during combat."""
        return []

    def get_block_actions(self, state: 'GameState', attackers: List['Card']) -> List[Action]:
        """Block actions during combat."""
        return []

    def get_response_actions(self, state: 'GameState') -> List[Action]:
        """Actions available when responding to a spell on the stack."""
        return []

    def on_upkeep(self, state: 'GameState') -> 'GameState':
        """Called at the beginning of owner's upkeep."""
        return state

    def on_end_turn(self, state: 'GameState') -> 'GameState':
        """Called at end of turn."""
        return state

    def is_creature(self) -> bool:
        """Return True if this card is currently a creature."""
        return False

    def is_land(self) -> bool:
        """Return True if this card is a land."""
        return False

    def get_mana_value(self) -> int:
        """Calculate total mana value (CMC) of this card."""
        total = getattr(self, 'generic_cost', 0)
        color_costs = getattr(self, 'color_costs', {})
        total += sum(color_costs.values())
        return total

    def get_mana_output(self) -> int:
        """Return how much mana this card produces when tapped."""
        return 0

    def tap_for_mana(self) -> int:
        """Tap this card for mana, applying any side effects. Returns mana produced.

        Override in subclasses with special tap effects (e.g., depletion lands).
        Returns the amount of mana actually produced.
        """
        if self.tapped:
            return 0
        self.tapped = True
        return self.get_mana_output()

    def should_sacrifice_after_tap(self) -> bool:
        """Return True if this card should be sacrificed after tapping for mana."""
        return False

    def get_signature_state(self) -> tuple:
        """Return hashable state tuple for memoization.

        Override in subclasses to include card-specific state.
        Base implementation returns minimal common fields.
        """
        return (self.name, self.tapped)

    @abstractmethod
    def copy(self) -> 'Card':
        """Create a deep copy of this card."""
        pass
