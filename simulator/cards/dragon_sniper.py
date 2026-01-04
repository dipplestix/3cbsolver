"""Dragon Sniper card for the 3CB simulator."""
from typing import List, TYPE_CHECKING

from .base import Action
from .creature import Creature

if TYPE_CHECKING:
    from ..solver import GameState


class DragonSniper(Creature):
    """
    Dragon Sniper - G
    Creature - Human Archer
    1/1
    Vigilance, Reach, Deathtouch
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Dragon Sniper",
            owner=owner,
            power=1,
            toughness=1,
            color_costs={'G': 1},
            keywords=['vigilance', 'reach', 'deathtouch']
        )

    @property
    def has_vigilance(self) -> bool:
        return True

    @property
    def has_reach(self) -> bool:
        return True

    @property
    def has_deathtouch(self) -> bool:
        return True

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        available = state.get_available_mana_by_color(self.owner)
        if available.get('G', 0) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            # Pay 1 green mana
            ns = s.pay_mana(self.owner, 'G', 1)
            # Move sniper from hand to battlefield
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    sniper = ns.hands[self.owner].pop(i)
                    sniper.entered_this_turn = True
                    ns.battlefield[self.owner].append(sniper)
                    break
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def get_attack_actions(self, state: 'GameState') -> List[Action]:
        """Attack without tapping due to vigilance."""
        if state.active_player != self.owner:
            return []
        if state.phase != "combat_attack":
            return []
        if self.tapped:
            return []
        if self.attacking:
            return []  # Already attacking
        if self.entered_this_turn:
            return []  # Summoning sickness

        def attack(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, DragonSniper):
                    card.attacking = True
                    # Vigilance: Don't tap when attacking
                    break
            return ns

        return [Action(f"Attack with {self.name}", attack)]

    def copy(self) -> 'DragonSniper':
        new_sniper = DragonSniper(self.owner)
        new_sniper.tapped = self.tapped
        new_sniper.damage = self.damage
        new_sniper.attacking = self.attacking
        new_sniper.entered_this_turn = self.entered_this_turn
        return new_sniper


def create_dragon_sniper(owner: int) -> DragonSniper:
    return DragonSniper(owner)
