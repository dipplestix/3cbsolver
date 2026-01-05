"""Creature base class for the 3CB simulator."""
from typing import List, Optional, Dict, TYPE_CHECKING

from .base import Card, Action, CardType

if TYPE_CHECKING:
    from ..solver import GameState


class Creature(Card):
    """A creature card with power and toughness."""

    def __init__(self, name: str, owner: int, power: int, toughness: int,
                 color_costs: Optional[Dict[str, int]] = None,
                 generic_cost: int = 0,
                 keywords: Optional[List[str]] = None,
                 creature_types: Optional[List[str]] = None):
        """Initialize creature.

        Args:
            color_costs: Dict of colored mana required, e.g. {'W': 1} for {W},
                        {'W': 2} for {W}{W}, {'B': 1, 'G': 1} for {B}{G}
            generic_cost: Generic mana required (can be paid with any color)
        """
        super().__init__(name, owner)
        self.power = power
        self.toughness = toughness
        self.color_costs = color_costs or {}  # e.g., {'W': 1} or {'B': 1, 'G': 1}
        self.generic_cost = generic_cost
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

    def is_creature(self) -> bool:
        """Creatures are always creatures."""
        return True

    def get_signature_state(self) -> tuple:
        """Return creature-specific state for memoization."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature - always True for Creature
            self.attacking,
            self.damage,
        )

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

        # Calculate total mana needed
        total_colored = sum(self.color_costs.values())
        total_needed = total_colored + self.generic_cost

        # Check total mana available
        if state.get_available_mana(self.owner) < total_needed:
            return []

        # Check each color requirement
        available = state.get_available_mana_by_color(self.owner)
        for color, amount in self.color_costs.items():
            if available.get(color, 0) < amount:
                return []

        # Capture costs for closure
        color_costs = self.color_costs.copy()
        generic_cost = self.generic_cost
        creature_name = self.name

        def cast(s: 'GameState') -> 'GameState':
            ns = s.copy()
            # Move card from hand to stack (not battlefield yet)
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == creature_name:
                    card_copy = ns.hands[self.owner].pop(i)
                    card_copy.entered_this_turn = True  # Will have summoning sickness when it resolves
                    ns.stack.append(card_copy)
                    break
            # Pay each colored cost
            for color, amount in color_costs.items():
                ns = ns.pay_mana(self.owner, color, amount)
            # Pay generic cost
            if generic_cost > 0:
                ns = ns.pay_generic_mana(self.owner, generic_cost)
            # Enter response phase to give opponent chance to respond
            ns.phase = "response"
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def resolve(self, state: 'GameState') -> 'GameState':
        """Resolve this creature spell from the stack to the battlefield."""
        ns = state.copy()
        # Move from stack to battlefield (the spell object is already removed from stack by caller)
        # Find ourselves in the original state's stack to get owner info
        ns.battlefield[self.owner].append(self)
        return ns

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
            color_costs=self.color_costs.copy(),
            generic_cost=self.generic_cost,
            keywords=self.keywords.copy(),
            creature_types=self.creature_types.copy()
        )
        new_creature.tapped = self.tapped
        new_creature.damage = self.damage
        new_creature.attacking = self.attacking
        new_creature.entered_this_turn = self.entered_this_turn
        new_creature.cant_be_blocked_by = self.cant_be_blocked_by.copy()
        return new_creature
