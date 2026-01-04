"""Soldier Token - 1/1 white creature token."""
from typing import List, TYPE_CHECKING

from .creature import Creature

if TYPE_CHECKING:
    from ..game_state import GameState


class SoldierToken(Creature):
    """A 1/1 white Soldier creature token with +1/+1 counter support."""

    def __init__(self, owner: int):
        super().__init__(
            name="Soldier",
            owner=owner,
            power=1,
            toughness=1,
            mana_cost=0,
            mana_color='',
            keywords=[],
            creature_types=['Soldier']
        )
        self.plus_counters = 0  # Support for +1/+1 counters

    @property
    def current_power(self) -> int:
        return self.power + self.plus_counters

    @property
    def current_toughness(self) -> int:
        return self.toughness + self.plus_counters

    def get_signature_state(self) -> tuple:
        """Return soldier-specific state including counters."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.plus_counters,
        )

    def get_play_actions(self, state: 'GameState') -> List:
        """Tokens can't be played from hand."""
        return []

    def copy(self) -> 'SoldierToken':
        token = SoldierToken(self.owner)
        token.tapped = self.tapped
        token.damage = self.damage
        token.attacking = self.attacking
        token.entered_this_turn = self.entered_this_turn
        token.plus_counters = self.plus_counters
        return token


def create_soldier_token(owner: int) -> SoldierToken:
    """Factory function for Soldier token."""
    return SoldierToken(owner)
