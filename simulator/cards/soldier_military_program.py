"""SOLDIER Military Program - Enchantment with combat trigger.

Scryfall Oracle Text:
---------------------
SOLDIER Military Program
{2}{W}
Enchantment

At the beginning of combat on your turn, choose one. If you control a commander,
you may choose both instead.
• Create a 1/1 white Soldier creature token.
• Put a +1/+1 counter on each of up to two Soldiers you control.

Note: In 3CB, there are no commanders, so always choose ONE mode.
"""
from typing import List, TYPE_CHECKING

from .enchantment import Enchantment
from .soldier_token import SoldierToken
from .base import Action

if TYPE_CHECKING:
    from ..game_state import GameState


class SoldierMilitaryProgram(Enchantment):
    """SOLDIER Military Program - creates soldiers or buffs them at combat."""

    def __init__(self, owner: int):
        super().__init__(
            name="SOLDIER Military Program",
            owner=owner,
            color_costs={'W': 1},
            generic_cost=2
        )
        self.combat_trigger_used = False

    def get_signature_state(self) -> tuple:
        """Return state for memoization including trigger status."""
        return (self.name, self.tapped, self.combat_trigger_used)

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """At beginning of combat on your turn, choose one mode.

        Mode 1: Create a 1/1 white Soldier creature token
        Mode 2: Put a +1/+1 counter on each of up to two Soldiers you control
        """
        if state.active_player != self.owner:
            return []
        if state.phase != "combat_attack":
            return []
        if self.combat_trigger_used:
            return []

        actions = []

        # Mode 1: Create a 1/1 Soldier token
        def create_soldier(s: 'GameState') -> 'GameState':
            ns = s.copy()
            # Mark trigger used
            for card in ns.enchantments[self.owner]:
                if card.name == self.name and isinstance(card, SoldierMilitaryProgram):
                    card.combat_trigger_used = True
                    break
            # Create token with summoning sickness
            token = SoldierToken(self.owner)
            token.entered_this_turn = True
            ns.battlefield[self.owner].append(token)
            return ns
        actions.append(Action("SOLDIER: Create 1/1 Soldier", create_soldier))

        # Mode 2: Put +1/+1 counter on each of up to two Soldiers
        # Only offer if we have soldiers to buff
        soldiers = [c for c in state.battlefield[self.owner]
                    if 'Soldier' in getattr(c, 'creature_types', [])]

        if soldiers:
            def buff_soldiers(s: 'GameState') -> 'GameState':
                ns = s.copy()
                # Mark trigger used
                for card in ns.enchantments[self.owner]:
                    if card.name == self.name and isinstance(card, SoldierMilitaryProgram):
                        card.combat_trigger_used = True
                        break
                # Buff up to 2 soldiers
                count = 0
                for card in ns.battlefield[self.owner]:
                    if 'Soldier' in getattr(card, 'creature_types', []) and count < 2:
                        if hasattr(card, 'plus_counters'):
                            card.plus_counters += 1
                        else:
                            card.plus_counters = 1
                        count += 1
                return ns
            num_soldiers = min(len(soldiers), 2)
            action_name = f"SOLDIER: +1/+1 on {num_soldiers} Soldier{'s' if num_soldiers > 1 else ''}"
            actions.append(Action(action_name, buff_soldiers))

        return actions

    def copy(self) -> 'SoldierMilitaryProgram':
        new_card = SoldierMilitaryProgram(self.owner)
        new_card.tapped = self.tapped
        new_card.combat_trigger_used = self.combat_trigger_used
        return new_card


def create_soldier_military_program(owner: int) -> SoldierMilitaryProgram:
    """Factory function for SOLDIER Military Program."""
    return SoldierMilitaryProgram(owner)
