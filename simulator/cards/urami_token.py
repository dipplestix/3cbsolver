"""Urami - Legendary 5/5 Demon Spirit token with flying."""
from typing import List, TYPE_CHECKING

from .creature import Creature
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class UramiToken(Creature):
    """
    Urami
    Legendary Creature Token — Demon Spirit
    5/5
    Flying
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Urami",
            owner=owner,
            power=5,
            toughness=5,
            color_costs={},
            generic_cost=0,
            keywords=['flying'],
            creature_types=['Demon', 'Spirit']
        )

    @property
    def has_flying(self) -> bool:
        return True

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        # Tokens can't be played from hand
        return []

    def copy(self) -> 'UramiToken':
        new_token = UramiToken(self.owner)
        new_token.tapped = self.tapped
        new_token.damage = self.damage
        new_token.attacking = self.attacking
        new_token.entered_this_turn = self.entered_this_turn
        return new_token


def create_urami_token(owner: int) -> UramiToken:
    """Factory function for Urami token."""
    return UramiToken(owner)
