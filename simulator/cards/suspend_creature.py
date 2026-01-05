"""Suspend creature base class for the 3CB simulator."""
from typing import List, Optional, Dict, TYPE_CHECKING

from .creature import Creature
from .base import Action

if TYPE_CHECKING:
    from ..game_state import GameState


class SuspendCreature(Creature):
    """A creature card with the Suspend ability.

    Suspend allows paying a reduced cost to exile the card with time counters.
    Each upkeep, a time counter is removed. When the last counter is removed,
    the creature enters the battlefield with haste.
    """

    def __init__(self, name: str, owner: int, power: int, toughness: int,
                 color_costs: Optional[Dict[str, int]] = None,
                 generic_cost: int = 0,
                 suspend_counters: int = 0,
                 suspend_color: str = '',
                 keywords: Optional[List[str]] = None,
                 creature_types: Optional[List[str]] = None):
        """Initialize suspend creature.

        Args:
            suspend_counters: Number of time counters when suspended
            suspend_color: Color of mana required to suspend (e.g., 'G', 'R')
        """
        super().__init__(name, owner, power, toughness,
                         color_costs=color_costs,
                         generic_cost=generic_cost,
                         keywords=keywords,
                         creature_types=creature_types)
        self.suspend_counters = suspend_counters  # Initial time counters when suspending
        self.suspend_color = suspend_color
        self.time_counters = 0  # Current time counters (when in exile)
        self.is_suspended = False  # True when in exile with time counters

    def get_signature_state(self) -> tuple:
        """Return suspend-specific state for memoization."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.time_counters,
            self.is_suspended,
        )

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        """Generate actions for playing this card.

        Options:
        1. Cast normally (if enough mana)
        2. Suspend (if have suspend color mana and card is in hand)
        """
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        actions = []

        # Option 1: Cast normally (check if enough mana)
        total_colored = sum(self.color_costs.values())
        total_needed = total_colored + self.generic_cost

        available = state.get_available_mana_by_color(self.owner)
        can_cast = state.get_available_mana(self.owner) >= total_needed
        if can_cast:
            for color, amount in self.color_costs.items():
                if available.get(color, 0) < amount:
                    can_cast = False
                    break

        if can_cast:
            color_costs = self.color_costs.copy()
            generic_cost = self.generic_cost

            def cast(s: 'GameState') -> 'GameState':
                ns = s.copy()
                for i, card in enumerate(ns.hands[self.owner]):
                    if card.name == self.name:
                        card_copy = ns.hands[self.owner].pop(i)
                        card_copy.entered_this_turn = True
                        ns.battlefield[self.owner].append(card_copy)
                        break
                for color, amount in color_costs.items():
                    ns = ns.pay_mana(self.owner, color, amount)
                if generic_cost > 0:
                    ns = ns.pay_generic_mana(self.owner, generic_cost)
                return ns

            actions.append(Action(f"Cast {self.name}", cast))

        # Option 2: Suspend (if have suspend color mana)
        if self.suspend_color and self.suspend_counters > 0:
            if available.get(self.suspend_color, 0) >= 1:
                suspend_color = self.suspend_color
                suspend_counters = self.suspend_counters

                def suspend(s: 'GameState') -> 'GameState':
                    ns = s.copy()
                    for i, card in enumerate(ns.hands[self.owner]):
                        if card.name == self.name:
                            card_copy = ns.hands[self.owner].pop(i)
                            card_copy.time_counters = suspend_counters
                            card_copy.is_suspended = True
                            ns.exile[self.owner].append(card_copy)
                            break
                    ns = ns.pay_mana(self.owner, suspend_color, 1)
                    return ns

                actions.append(Action(f"Suspend {self.name} ({self.suspend_counters} counters)", suspend))

        return actions

    def copy(self) -> 'SuspendCreature':
        new_creature = SuspendCreature(
            self.name, self.owner, self.power, self.toughness,
            color_costs=self.color_costs.copy(),
            generic_cost=self.generic_cost,
            suspend_counters=self.suspend_counters,
            suspend_color=self.suspend_color,
            keywords=self.keywords.copy(),
            creature_types=self.creature_types.copy()
        )
        new_creature.tapped = self.tapped
        new_creature.damage = self.damage
        new_creature.attacking = self.attacking
        new_creature.entered_this_turn = self.entered_this_turn
        new_creature.cant_be_blocked_by = self.cant_be_blocked_by.copy()
        new_creature.time_counters = self.time_counters
        new_creature.is_suspended = self.is_suspended
        return new_creature
