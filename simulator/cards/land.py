"""Land cards for the 3CB simulator.

Scryfall Oracle Text (Basic Lands):
-----------------------------------
Plains - Basic Land — Plains
(T: Add W.)

Island - Basic Land — Island
(T: Add U.)

Forest - Basic Land — Forest
(T: Add G.)
"""
from typing import List, Optional, TYPE_CHECKING

from .base import Card, Action, CardType

if TYPE_CHECKING:
    from ..solver import GameState


class Land(Card):
    """A land card that produces mana."""

    def __init__(self, name: str, owner: int, mana_produced: str):
        super().__init__(name, owner)
        self.mana_produced = mana_produced
        self.card_type = CardType.LAND
        self.entered_this_turn = False

    def get_mana_output(self) -> int:
        """Basic lands produce 1 mana."""
        return 1

    def get_signature_state(self) -> tuple:
        """Return land-specific state for memoization."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
        )

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.land_played_this_turn:
            return []
        if state.phase != "main1":
            return []

        def play_land(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    card_copy = ns.hands[self.owner].pop(i)
                    card_copy.entered_this_turn = True
                    ns.battlefield[self.owner].append(card_copy)
                    break
            ns.land_played_this_turn = True
            # Trigger landfall for any creatures that care
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'plus_counters'):
                    card.plus_counters += 1
            return ns

        return [Action(f"Play {self.name}", play_land)]

    def copy(self) -> 'Land':
        new_land = Land(self.name, self.owner, self.mana_produced)
        new_land.tapped = self.tapped
        new_land.entered_this_turn = self.entered_this_turn
        return new_land


class CreatureLand(Land):
    """A land that can become a creature (e.g., Mutavault)."""

    def __init__(self, name: str, owner: int, mana_produced: str,
                 activation_cost: int, creature_power: int, creature_toughness: int,
                 creature_keywords: Optional[List[str]] = None,
                 creature_types: Optional[List[str]] = None,
                 all_creature_types: bool = False):
        super().__init__(name, owner, mana_produced)
        self.activation_cost = activation_cost
        self.creature_power = creature_power
        self.creature_toughness = creature_toughness
        self.creature_keywords = creature_keywords or []
        self.creature_types = creature_types or []
        self.all_creature_types = all_creature_types  # For Mutavault
        self._is_creature = False
        self.damage = 0
        self.attacking = False

    def is_creature(self) -> bool:
        """CreatureLand is a creature only when activated."""
        return self._is_creature

    def get_signature_state(self) -> tuple:
        """Return creature-land-specific state for memoization."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            self._is_creature,
            self.attacking,
            self.damage,
        )

    @property
    def power(self) -> int:
        return self.creature_power if self._is_creature else 0

    @property
    def toughness(self) -> int:
        return self.creature_toughness if self._is_creature else 0

    @property
    def is_alive(self) -> bool:
        if not self._is_creature:
            return True
        return self.toughness > self.damage

    @property
    def has_flying(self) -> bool:
        return self._is_creature and 'flying' in self.creature_keywords

    def can_attack(self) -> bool:
        """CreatureLand can attack if it's a creature, untapped, and doesn't have summoning sickness."""
        if not self._is_creature or self.tapped:
            return False
        return not self.entered_this_turn

    def can_block(self, attacker) -> bool:
        if not self._is_creature or self.tapped:
            return False
        if hasattr(attacker, 'has_flying') and attacker.has_flying:
            if not self.has_flying and 'reach' not in self.creature_keywords:
                return False
        # Check if attacker can't be blocked by this creature's types
        if hasattr(attacker, 'cant_be_blocked_by'):
            for blocked_type in attacker.cant_be_blocked_by:
                if blocked_type in self.creature_types:
                    return False
                # Mutavault has all creature types
                if self.all_creature_types:
                    return False
        return True

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        own_main = (state.active_player == self.owner and state.phase == "main1")
        opponent_combat = (state.active_player != self.owner and state.phase == "combat_block")

        if not own_main and not opponent_combat:
            return []
        if self._is_creature:
            return []
        if self.tapped:
            return []

        available_mana = 0
        for card in state.battlefield[self.owner]:
            if card.name != self.name:
                if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                    available_mana += 1
        for card in state.artifacts[self.owner]:
            if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                available_mana += 1

        if available_mana < self.activation_cost:
            return []

        def activate(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, CreatureLand):
                    card._is_creature = True
                    break
            mana_needed = self.activation_cost
            for card in ns.artifacts[self.owner]:
                if mana_needed <= 0:
                    break
                if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                    card.tapped = True
                    mana_needed -= 1
            for card in ns.battlefield[self.owner]:
                if mana_needed <= 0:
                    break
                if card.name != self.name:
                    if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                        card.tapped = True
                        mana_needed -= 1
            return ns

        return [Action(f"Activate {self.name}", activate)]

    def get_attack_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if not self._is_creature:
            return []
        if self.tapped:
            return []
        if self.entered_this_turn:
            return []

        def attack(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, CreatureLand):
                    card.attacking = True
                    card.tapped = True
                    break
            return ns

        return [Action(f"Attack with {self.name}", attack)]

    def get_block_actions(self, state: 'GameState', attackers_with_idx: List[tuple]) -> List[Action]:
        """Generate blocking actions for creature lands.

        Args:
            state: Current game state
            attackers_with_idx: List of (attacker_battlefield_idx, attacker) tuples
        """
        if state.active_player == self.owner:
            return []
        if not self._is_creature:
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

    def on_end_turn(self, state: 'GameState') -> 'GameState':
        self._is_creature = False
        self.damage = 0
        self.attacking = False
        return state

    def copy(self) -> 'CreatureLand':
        new_land = CreatureLand(
            self.name, self.owner, self.mana_produced,
            self.activation_cost, self.creature_power, self.creature_toughness,
            self.creature_keywords.copy() if self.creature_keywords else [],
            self.creature_types.copy() if self.creature_types else [],
            self.all_creature_types
        )
        new_land.tapped = self.tapped
        new_land._is_creature = self._is_creature
        new_land.damage = self.damage
        new_land.attacking = self.attacking
        new_land.entered_this_turn = self.entered_this_turn
        return new_land


# Factory functions
def create_island(owner: int) -> Land:
    return Land("Island", owner, 'U')


def create_forest(owner: int) -> Land:
    return Land("Forest", owner, 'G')


def create_plains(owner: int) -> Land:
    return Land("Plains", owner, 'W')
