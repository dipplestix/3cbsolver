"""Creature base class for the 3CB simulator."""
from typing import List, Optional, TYPE_CHECKING

from .base import Card, Action, CardType

if TYPE_CHECKING:
    from ..solver import GameState


class Creature(Card):
    """A creature card with power and toughness."""

    def __init__(self, name: str, owner: int, power: int, toughness: int,
                 mana_cost: int = 0, mana_color: str = '',
                 keywords: Optional[List[str]] = None,
                 creature_types: Optional[List[str]] = None):
        super().__init__(name, owner)
        self.power = power
        self.toughness = toughness
        self.mana_cost = mana_cost
        self.mana_color = mana_color
        self.keywords = keywords or []
        self.creature_types = creature_types or []  # e.g., ['Vampire', 'Noble'], ['Human', 'Soldier']
        self.damage = 0
        self.attacking = False
        self.card_type = CardType.CREATURE
        self.entered_this_turn = False
        # For creatures that can't be blocked by certain types
        self.cant_be_blocked_by: List[str] = []

    @property
    def is_alive(self) -> bool:
        return self.toughness > self.damage

    @property
    def has_flying(self) -> bool:
        return 'flying' in self.keywords

    def can_attack(self) -> bool:
        return not self.tapped and not self.entered_this_turn

    def can_block(self, attacker) -> bool:
        if self.tapped:
            return False
        if hasattr(attacker, 'has_flying') and attacker.has_flying:
            if not self.has_flying and 'reach' not in self.keywords:
                return False
        # Check if attacker can't be blocked by this creature's types
        if hasattr(attacker, 'cant_be_blocked_by'):
            for blocked_type in attacker.cant_be_blocked_by:
                # Check creature_types list
                if blocked_type in self.creature_types:
                    return False
                # Check all_creature_types flag (e.g., Mutavault has all types)
                if getattr(self, 'all_creature_types', False):
                    return False
        return True

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        if self.mana_color:
            available = state.get_available_mana_by_color(self.owner)
            if available.get(self.mana_color, 0) < self.mana_cost:
                return []
        else:
            if state.get_available_mana(self.owner) < self.mana_cost:
                return []

        def cast(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    card_copy = ns.hands[self.owner].pop(i)
                    card_copy.entered_this_turn = True
                    ns.battlefield[self.owner].append(card_copy)
                    break
            if self.mana_color:
                for card in ns.battlefield[self.owner]:
                    if (hasattr(card, 'mana_produced') and
                        card.mana_produced == self.mana_color and
                        not card.tapped):
                        card.tapped = True
                        break
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def get_attack_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if not self.can_attack():
            return []

        def attack(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, Creature):
                    card.attacking = True
                    card.tapped = True
                    break
            return ns

        return [Action(f"Attack with {self.name}", attack)]

    def get_block_actions(self, state: 'GameState', attackers_with_idx: List[tuple]) -> List[Action]:
        """Generate blocking actions.

        Args:
            state: Current game state
            attackers_with_idx: List of (attacker_battlefield_idx, attacker) tuples
        """
        if state.active_player == self.owner:
            return []
        if self.tapped:
            return []

        # Find this blocker's index in the defender's battlefield
        defender = 1 - state.active_player
        blocker_idx = None
        for i, card in enumerate(state.battlefield[defender]):
            if card is self:
                blocker_idx = i
                break
        if blocker_idx is None:
            return []

        # Check if this blocker is already assigned to block something
        if blocker_idx in state.blocking_assignments.values():
            return []

        actions = []
        for att_idx, attacker in attackers_with_idx:
            # Skip if this attacker is already being blocked
            if att_idx in state.blocking_assignments:
                continue
            if self.can_block(attacker):
                def make_block(attacker_bf_idx, blocker_bf_idx):
                    def block(s: 'GameState') -> 'GameState':
                        ns = s.copy()
                        ns.blocking_assignments[attacker_bf_idx] = blocker_bf_idx
                        return ns
                    return block
                actions.append(Action(f"Block {attacker.name} with {self.name}",
                                     make_block(att_idx, blocker_idx)))
        return actions

    def copy(self) -> 'Creature':
        new_creature = Creature(
            self.name, self.owner, self.power, self.toughness,
            self.mana_cost, self.mana_color, self.keywords.copy(),
            self.creature_types.copy()
        )
        new_creature.tapped = self.tapped
        new_creature.damage = self.damage
        new_creature.attacking = self.attacking
        new_creature.entered_this_turn = self.entered_this_turn
        new_creature.cant_be_blocked_by = self.cant_be_blocked_by.copy()
        return new_creature
