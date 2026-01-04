"""Scythe Tiger card for the 3CB simulator.

Scryfall Oracle Text:
---------------------
Scythe Tiger {G}
Creature — Cat

Shroud (This creature can't be the target of spells or abilities.)
When this creature enters, sacrifice it unless you sacrifice a land.

3/2

Implementation Notes:
- Shroud is not relevant (no targeting in this simulator)
- Land sacrifice is mandatory on cast (handled in get_play_actions)
"""
from typing import List, TYPE_CHECKING

from .base import Action
from .creature import Creature
from .land import Land, CreatureLand

if TYPE_CHECKING:
    from ..solver import GameState


class ScytheTiger(Creature):
    """Scythe Tiger - a 3/2 that requires sacrificing a land to keep."""

    def __init__(self, owner: int):
        super().__init__(
            name="Scythe Tiger",
            owner=owner,
            power=3,
            toughness=2,
            color_costs={'G': 1},
            keywords=['shroud']
        )
        self.sacrificed_land = False

    @property
    def has_shroud(self) -> bool:
        return True

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        available = state.get_available_mana_by_color(self.owner)
        if available.get('G', 0) < 1:
            return []

        lands_on_battlefield = [c for c in state.battlefield[self.owner]
                                if isinstance(c, (Land, CreatureLand))]

        if len(lands_on_battlefield) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            # Pay 1 green mana
            ns = s.pay_mana(self.owner, 'G', 1)

            # Move tiger from hand to battlefield
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    tiger = ns.hands[self.owner].pop(i)
                    tiger.entered_this_turn = True
                    ns.battlefield[self.owner].append(tiger)
                    break

            # Sacrifice a land (ETB trigger)
            for i, card in enumerate(ns.battlefield[self.owner]):
                if isinstance(card, (Land, CreatureLand)):
                    sacrificed = ns.battlefield[self.owner].pop(i)
                    ns.graveyard[self.owner].append(sacrificed)
                    break

            return ns

        return [Action(f"Cast {self.name} (sacrifice a land)", cast)]

    def copy(self) -> 'ScytheTiger':
        new_tiger = ScytheTiger(self.owner)
        new_tiger.tapped = self.tapped
        new_tiger.damage = self.damage
        new_tiger.attacking = self.attacking
        new_tiger.entered_this_turn = self.entered_this_turn
        return new_tiger


def create_scythe_tiger(owner: int) -> ScytheTiger:
    return ScytheTiger(owner)
