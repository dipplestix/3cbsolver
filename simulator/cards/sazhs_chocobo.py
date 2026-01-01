"""Sazh's Chocobo card for the 3CB simulator."""
from typing import List, TYPE_CHECKING

from .base import Action
from .creature import Creature
from .undiscovered_paradise import UndiscoveredParadise

if TYPE_CHECKING:
    from ..solver import GameState


class SazhsChocobo(Creature):
    """
    Sazh's Chocobo - G
    Creature - Bird
    0/1
    Landfall - Whenever a land you control enters, put a +1/+1 counter on this creature.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Sazh's Chocobo",
            owner=owner,
            power=0,
            toughness=1,
            mana_cost=1,
            mana_color='any',
            keywords=[]
        )
        self.plus_counters = 0

    @property
    def current_power(self) -> int:
        return self.power + self.plus_counters

    @property
    def current_toughness(self) -> int:
        return self.toughness + self.plus_counters

    def can_block(self, attacker) -> bool:
        if self.tapped:
            return False
        if hasattr(attacker, 'has_flying') and attacker.has_flying:
            return False
        return True

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        if state.get_available_mana(self.owner) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    chocobo = ns.hands[self.owner].pop(i)
                    chocobo.entered_this_turn = True
                    ns.battlefield[self.owner].append(chocobo)
                    break
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                    card.tapped = True
                    if isinstance(card, UndiscoveredParadise):
                        card.return_to_hand = True
                    break
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def copy(self) -> 'SazhsChocobo':
        new_chocobo = SazhsChocobo(self.owner)
        new_chocobo.tapped = self.tapped
        new_chocobo.damage = self.damage
        new_chocobo.attacking = self.attacking
        new_chocobo.entered_this_turn = self.entered_this_turn
        new_chocobo.plus_counters = self.plus_counters
        return new_chocobo


def create_sazhs_chocobo(owner: int) -> SazhsChocobo:
    return SazhsChocobo(owner)
