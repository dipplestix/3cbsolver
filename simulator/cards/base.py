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

    def on_upkeep(self, state: 'GameState') -> 'GameState':
        """Called at the beginning of owner's upkeep."""
        return state

    def on_end_turn(self, state: 'GameState') -> 'GameState':
        """Called at end of turn."""
        return state

    @abstractmethod
    def copy(self) -> 'Card':
        """Create a deep copy of this card."""
        pass
