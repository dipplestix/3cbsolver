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
            color_costs={'W': 1},
            generic_cost=1,
            keywords=[],
            creature_types=['Human', 'Cleric']
        )
        self.plus_counters = 0
        self.combat_trigger_used = False  # Track if we've used the trigger this turn

    def get_signature_state(self) -> tuple:
        """Return aspirant-specific state including counters and trigger state."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.plus_counters,
            self.combat_trigger_used,
        )

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

        # Need 1W (1 generic + 1 white)
        # Check total mana available
        if state.get_available_mana(self.owner) < 2:
            return []

        # Check white mana available
        available = state.get_available_mana_by_color(self.owner)
        if available.get('W', 0) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            # Pay 1 white mana
            ns = s.pay_mana(self.owner, 'W', 1)
            # Pay 1 generic mana
            ns = ns.pay_generic_mana(self.owner, 1)

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

        # Check if we should auto-apply trigger (only creature on battlefield)
        creatures = [c for c in state.battlefield[self.owner] if hasattr(c, 'power')]
        auto_apply_trigger = (len(creatures) == 1 and creatures[0].name == self.name
                              and not self.combat_trigger_used)

        def attack(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, LuminarchAspirant):
                    # Auto-apply trigger if we're the only creature
                    if auto_apply_trigger:
                        card.plus_counters += 1
                        card.combat_trigger_used = True
                    card.attacking = True
                    card.tapped = True
                    break
            return ns

        return [Action(f"Attack with {self.name}", attack)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """At beginning of combat, put +1/+1 counter on target creature you control.

        Auto-applies the trigger when Aspirant is the only creature (always optimal).
        """
        if state.active_player != self.owner:
            return []
        # Trigger at combat_attack phase before declaring attackers
        if state.phase != "combat_attack":
            return []
        if self.combat_trigger_used:
            return []

        # Find all creatures we control
        creatures = []
        for card in state.battlefield[self.owner]:
            if hasattr(card, 'power'):
                creatures.append(card)

        # If Aspirant is the only creature, auto-apply trigger (no choice needed)
        if len(creatures) == 1 and creatures[0].name == self.name:
            def buff_self(s: 'GameState') -> 'GameState':
                ns = s.copy()
                for c in ns.battlefield[self.owner]:
                    if c.name == self.name and isinstance(c, LuminarchAspirant):
                        c.combat_trigger_used = True
                        c.plus_counters += 1
                        break
                return ns
            # Return single mandatory action - solver will take it automatically
            return [Action("Aspirant: +1/+1 on self", buff_self)]

        # Multiple creatures - offer choices, but it's a mandatory trigger
        # so we ONLY return trigger actions (not attack actions)
        # The attack phase will be handled after trigger resolves
        actions = []
        seen_names = set()
        for card in creatures:
            if card.name in seen_names:
                continue
            seen_names.add(card.name)

            def make_buff_action(creature_name):
                def buff_creature(s: 'GameState') -> 'GameState':
                    ns = s.copy()
                    for c in ns.battlefield[self.owner]:
                        if c.name == self.name and isinstance(c, LuminarchAspirant):
                            c.combat_trigger_used = True
                            break
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
