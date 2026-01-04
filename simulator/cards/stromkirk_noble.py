"""Stromkirk Noble - Vampire that grows when dealing combat damage."""
from typing import List, TYPE_CHECKING

from .creature import Creature
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class StromkirkNoble(Creature):
    """
    Stromkirk Noble - R
    Creature — Vampire Noble
    1/1

    Stromkirk Noble can't be blocked by Humans.
    Whenever Stromkirk Noble deals combat damage to a player,
    put a +1/+1 counter on it.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Stromkirk Noble",
            owner=owner,
            power=1,
            toughness=1,
            color_costs={'R': 1},
            keywords=[],
            creature_types=['Vampire', 'Noble']
        )
        self.plus_counters = 0  # +1/+1 counters
        self.cant_be_blocked_by = ['Human']

    def get_signature_state(self) -> tuple:
        """Return noble-specific state including +1/+1 counters."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.plus_counters,
        )

    @property
    def current_power(self) -> int:
        return self.power + self.plus_counters

    @property
    def current_toughness(self) -> int:
        return self.toughness + self.plus_counters

    def on_deal_combat_damage_to_player(self, state: 'GameState') -> 'GameState':
        """Called when this creature deals combat damage to a player."""
        ns = state.copy()
        for card in ns.battlefield[self.owner]:
            if card.name == self.name:
                card.plus_counters += 1
                break
        return ns

    def copy(self) -> 'StromkirkNoble':
        new_creature = StromkirkNoble(self.owner)
        new_creature.tapped = self.tapped
        new_creature.damage = self.damage
        new_creature.attacking = self.attacking
        new_creature.entered_this_turn = self.entered_this_turn
        new_creature.plus_counters = self.plus_counters
        return new_creature


def create_stromkirk_noble(owner: int) -> StromkirkNoble:
    """Factory function for Stromkirk Noble."""
    return StromkirkNoble(owner)
