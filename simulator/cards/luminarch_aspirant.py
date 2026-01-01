"""Luminarch Aspirant - Creature that buffs at beginning of combat."""
from typing import List, TYPE_CHECKING

from .creature import Creature
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class LuminarchAspirant(Creature):
    """
    Luminarch Aspirant - 1W
    Creature — Human Cleric
    1/1

    At the beginning of combat on your turn, put a +1/+1 counter
    on target creature you control.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Luminarch Aspirant",
            owner=owner,
            power=1,
            toughness=1,
            mana_cost=2,
            mana_color='W',
            keywords=[],
            creature_types=['Human', 'Cleric']
        )
        self.plus_counters = 0
        self.combat_trigger_used = False  # Track if we've used the trigger this turn

    @property
    def current_power(self) -> int:
        return self.power + self.plus_counters

    @property
    def current_toughness(self) -> int:
        return self.toughness + self.plus_counters

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        # Need 2 white mana (1W cost)
        available = state.get_available_mana_by_color(self.owner)
        if available.get('W', 0) < 2:
            return []

        def cast(s: 'GameState') -> 'GameState':
            # Pay mana first
            ns = s.pay_mana(self.owner, 'W', 2)

            # Remove from hand and put on battlefield
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    aspirant = ns.hands[self.owner].pop(i)
                    aspirant.entered_this_turn = True
                    ns.battlefield[self.owner].append(aspirant)
                    break

            return ns

        return [Action(f"Cast {self.name}", cast)]

    def get_attack_actions(self, state: 'GameState') -> List[Action]:
        """Override to handle combat trigger before attacking."""
        if state.active_player != self.owner:
            return []
        if state.phase != "combat_attack":
            return []
        if self.tapped:
            return []
        if self.attacking:
            return []
        if self.entered_this_turn:
            return []  # Summoning sickness

        # Standard attack action
        def attack(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, LuminarchAspirant):
                    card.attacking = True
                    card.tapped = True
                    break
            return ns

        return [Action(f"Attack with {self.name}", attack)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """At beginning of combat, put +1/+1 counter on target creature you control."""
        if state.active_player != self.owner:
            return []
        # Trigger at combat_attack phase before declaring attackers
        if state.phase != "combat_attack":
            return []
        if self.combat_trigger_used:
            return []

        actions = []
        # Can target any creature we control
        # Deduplicate identical creatures (e.g., multiple Saprolings) to reduce branching
        seen_names = set()
        for card in state.battlefield[self.owner]:
            if not hasattr(card, 'power'):  # Not a creature
                continue
            if card.name in seen_names:
                continue  # Skip duplicates
            seen_names.add(card.name)

            def make_buff_action(creature_name):
                def buff_creature(s: 'GameState') -> 'GameState':
                    ns = s.copy()
                    # Mark trigger as used
                    for c in ns.battlefield[self.owner]:
                        if c.name == self.name and isinstance(c, LuminarchAspirant):
                            c.combat_trigger_used = True
                            break
                    # Add counter to target
                    for c in ns.battlefield[self.owner]:
                        if c.name == creature_name:
                            if hasattr(c, 'plus_counters'):
                                c.plus_counters += 1
                            else:
                                c.plus_counters = 1
                            break
                    return ns
                return buff_creature

            actions.append(Action(
                f"Aspirant: +1/+1 on {card.name}",
                make_buff_action(card.name)
            ))

        return actions

    def copy(self) -> 'LuminarchAspirant':
        new_aspirant = LuminarchAspirant(self.owner)
        new_aspirant.tapped = self.tapped
        new_aspirant.damage = self.damage
        new_aspirant.attacking = self.attacking
        new_aspirant.entered_this_turn = self.entered_this_turn
        new_aspirant.plus_counters = self.plus_counters
        new_aspirant.combat_trigger_used = self.combat_trigger_used
        return new_aspirant


def create_luminarch_aspirant(owner: int) -> LuminarchAspirant:
    """Factory function for Luminarch Aspirant."""
    return LuminarchAspirant(owner)
