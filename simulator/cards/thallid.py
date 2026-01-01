"""Thallid - Fungus creature that creates Saproling tokens.

Thallid (G)
Creature — Fungus (1/1)
At the beginning of your upkeep, put a spore counter on this creature.
Remove three spore counters from this creature: Create a 1/1 green Saproling creature token.
"""
from typing import List, TYPE_CHECKING

from .creature import Creature
from .base import Action
from .saproling_token import SaprolingToken

if TYPE_CHECKING:
    from ..solver import GameState


class Thallid(Creature):
    """Thallid - 1/1 Fungus that generates spore counters and creates Saprolings."""

    def __init__(self, owner: int):
        super().__init__(
            name="Thallid",
            owner=owner,
            power=1,
            toughness=1,
            mana_cost=1,
            mana_color='G',
            keywords=[],
            creature_types=['Fungus']
        )
        self.spore_counters = 0
        self.eot_power_boost = 0
        self.eot_toughness_boost = 0

    def on_upkeep(self, state: 'GameState') -> 'GameState':
        """At beginning of upkeep, put a spore counter on Thallid.

        Also auto-create Saproling when we hit 3 counters (to reduce branching).
        """
        ns = state.copy()
        for card in ns.battlefield[self.owner]:
            if card.name == self.name and isinstance(card, Thallid):
                card.spore_counters += 1
                # Auto-create saproling at 3 counters to reduce branching
                if card.spore_counters >= 3:
                    card.spore_counters -= 3
                    saproling = SaprolingToken(self.owner)
                    saproling.entered_this_turn = True
                    ns.battlefield[self.owner].append(saproling)
                break
        return ns

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Saproling creation is now automatic in upkeep."""
        # Token creation moved to on_upkeep to reduce branching
        return []

    def copy(self) -> 'Thallid':
        t = Thallid(self.owner)
        t.tapped = self.tapped
        t.damage = self.damage
        t.attacking = self.attacking
        t.entered_this_turn = self.entered_this_turn
        t.spore_counters = self.spore_counters
        t.eot_power_boost = self.eot_power_boost
        t.eot_toughness_boost = self.eot_toughness_boost
        return t


def create_thallid(owner: int) -> Thallid:
    """Factory function for Thallid."""
    return Thallid(owner)
