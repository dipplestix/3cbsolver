"""Heartfire Hero - Mouse Soldier with Valiant and death trigger."""
from typing import List, TYPE_CHECKING

from .creature import Creature
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class HeartfireHero(Creature):
    """
    Heartfire Hero - R
    Creature — Mouse Soldier
    1/1

    Valiant — Whenever this creature becomes the target of a spell or ability
    you control for the first time each turn, put a +1/+1 counter on it.

    When this creature dies, it deals damage equal to its power to each opponent.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Heartfire Hero",
            owner=owner,
            power=1,
            toughness=1,
            color_costs={'R': 1},
            keywords=[],
            creature_types=['Mouse', 'Soldier']
        )
        self.plus_counters = 0
        self.targeted_this_turn = False  # Track Valiant trigger

    def get_signature_state(self) -> tuple:
        """Return hero-specific state including counters and trigger state."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.plus_counters,
            self.targeted_this_turn,
        )

    @property
    def current_power(self) -> int:
        return self.power + self.plus_counters

    @property
    def current_toughness(self) -> int:
        return self.toughness + self.plus_counters

    def on_become_target(self, state: 'GameState') -> 'GameState':
        """Called when this creature becomes the target of a spell/ability you control."""
        ns = state.copy()
        for card in ns.battlefield[self.owner]:
            if card.name == self.name:
                if not card.targeted_this_turn:
                    card.targeted_this_turn = True
                    card.plus_counters += 1
                break
        return ns

    def on_death(self, state: 'GameState') -> 'GameState':
        """When this creature dies, deal damage equal to power to each opponent."""
        ns = state.copy()
        damage = self.current_power
        # Deal damage to opponent
        opponent = 1 - self.owner
        ns.life[opponent] -= damage
        # Check for game over
        if ns.life[opponent] <= 0:
            ns.game_over = True
            ns.winner = self.owner
        return ns

    def copy(self) -> 'HeartfireHero':
        new_creature = HeartfireHero(self.owner)
        new_creature.tapped = self.tapped
        new_creature.damage = self.damage
        new_creature.attacking = self.attacking
        new_creature.entered_this_turn = self.entered_this_turn
        new_creature.plus_counters = self.plus_counters
        new_creature.targeted_this_turn = self.targeted_this_turn
        return new_creature


def create_heartfire_hero(owner: int) -> HeartfireHero:
    """Factory function for Heartfire Hero."""
    return HeartfireHero(owner)
