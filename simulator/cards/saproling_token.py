"""Saproling Token - 1/1 green creature token."""
from typing import List, TYPE_CHECKING

from .creature import Creature

if TYPE_CHECKING:
    from ..solver import GameState


class SaprolingToken(Creature):
    """A 1/1 green Saproling creature token."""

    def __init__(self, owner: int):
        super().__init__(
            name="Saproling",
            owner=owner,
            power=1,
            toughness=1,
            mana_cost=0,
            mana_color='',
            keywords=[],
            creature_types=['Saproling']
        )
        self.eot_power_boost = 0
        self.eot_toughness_boost = 0

    def get_signature_state(self) -> tuple:
        """Return saproling-specific state including boosts."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.eot_power_boost,
            self.eot_toughness_boost,
        )

    def get_play_actions(self, state: 'GameState') -> List:
        """Tokens can't be played from hand."""
        return []

    def copy(self) -> 'SaprolingToken':
        token = SaprolingToken(self.owner)
        token.tapped = self.tapped
        token.damage = self.damage
        token.attacking = self.attacking
        token.entered_this_turn = self.entered_this_turn
        token.eot_power_boost = self.eot_power_boost
        token.eot_toughness_boost = self.eot_toughness_boost
        return token


def create_saproling_token(owner: int) -> SaprolingToken:
    """Factory function for Saproling token."""
    return SaprolingToken(owner)
