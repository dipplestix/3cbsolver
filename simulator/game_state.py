"""Game state representation for the 3CB simulator."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .cards import Card, Creature, CreatureLand


@dataclass
class GameState:
    """Represents the complete state of a game."""

    life: List[int] = field(default_factory=lambda: [20, 20])
    hands: List[List['Card']] = field(default_factory=lambda: [[], []])
    battlefield: List[List['Card']] = field(default_factory=lambda: [[], []])
    artifacts: List[List['Card']] = field(default_factory=lambda: [[], []])
    graveyard: List[List['Card']] = field(default_factory=lambda: [[], []])

    active_player: int = 0
    phase: str = "main1"  # untap, upkeep, main1, combat_attack, combat_block, combat_damage, end_turn
    turn: int = 1
    land_played_this_turn: bool = False

    # Combat tracking
    blocking_assignments: Dict[int, int] = field(default_factory=dict)  # attacker_idx -> blocker_battlefield_idx

    # Game end
    game_over: bool = False
    winner: Optional[int] = None  # None = draw, 0 or 1 = that player wins

    def copy(self) -> 'GameState':
        """Create a deep copy of this state."""
        return GameState(
            life=self.life.copy(),
            hands=[[c.copy() for c in self.hands[0]], [c.copy() for c in self.hands[1]]],
            battlefield=[[c.copy() for c in self.battlefield[0]], [c.copy() for c in self.battlefield[1]]],
            artifacts=[[c.copy() for c in self.artifacts[0]], [c.copy() for c in self.artifacts[1]]],
            graveyard=[[c.copy() for c in self.graveyard[0]], [c.copy() for c in self.graveyard[1]]],
            active_player=self.active_player,
            phase=self.phase,
            turn=self.turn,
            land_played_this_turn=self.land_played_this_turn,
            blocking_assignments=self.blocking_assignments.copy(),
            game_over=self.game_over,
            winner=self.winner
        )

    def get_available_mana(self, player: int) -> int:
        """Get total available (untapped) mana for a player."""
        total = 0
        for card in self.battlefield[player]:
            if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                # Creature lands (like Dryad Arbor) have summoning sickness
                if hasattr(card, 'power') and getattr(card, 'entered_this_turn', False):
                    continue  # Can't tap creature for mana with summoning sickness
                total += self._get_mana_amount(card)
        for card in self.artifacts[player]:
            if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                total += 1
        return total

    def _get_mana_amount(self, card) -> int:
        """Get how much mana a single card produces when tapped."""
        # Depletion lands (Remote Farm) produce 2 mana per tap
        if hasattr(card, 'depletion_counters') and card.depletion_counters > 0:
            return 2
        # Storage lands (Bottomless Vault) produce mana equal to counters
        if hasattr(card, 'storage_counters') and card.storage_counters > 0:
            return card.storage_counters
        # Regular lands produce 1
        return 1

    def get_available_mana_by_color(self, player: int) -> Dict[str, int]:
        """Get available mana by color for a player."""
        mana = {}
        for card in self.battlefield[player]:
            if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                # Creature lands (like Dryad Arbor) have summoning sickness
                if hasattr(card, 'power') and getattr(card, 'entered_this_turn', False):
                    continue  # Can't tap creature for mana with summoning sickness
                color = card.mana_produced
                amount = self._get_mana_amount(card)
                mana[color] = mana.get(color, 0) + amount
        for card in self.artifacts[player]:
            if hasattr(card, 'mana_produced') and card.mana_produced and not card.tapped:
                color = card.mana_produced
                mana[color] = mana.get(color, 0) + 1
        return mana

    def pay_mana(self, player: int, color: str, amount: int) -> 'GameState':
        """Pay mana of a specific color, handling special lands. Returns new state."""
        ns = self.copy()
        remaining = amount

        # Sort lands to use special lands efficiently
        lands = [c for c in ns.battlefield[player]
                 if hasattr(c, 'mana_produced') and c.mana_produced == color and not c.tapped]

        for card in lands:
            if remaining <= 0:
                break

            # Skip creature lands with summoning sickness
            if hasattr(card, 'power') and getattr(card, 'entered_this_turn', False):
                continue

            if hasattr(card, 'depletion_counters') and card.depletion_counters > 0:
                # Depletion land: produces 2, removes counter, may sacrifice
                card.tapped = True
                card.depletion_counters -= 1
                remaining -= 2
                if card.depletion_counters <= 0:
                    ns.battlefield[player].remove(card)
                    ns.graveyard[player].append(card)
            elif hasattr(card, 'storage_counters') and card.storage_counters > 0:
                # Storage land: produces all counters at once
                mana_from_storage = min(card.storage_counters, remaining)
                card.storage_counters -= mana_from_storage
                card.tapped = True
                remaining -= mana_from_storage
            else:
                # Regular land: produces 1
                card.tapped = True
                remaining -= 1

        return ns

    def get_attackers(self) -> List['Card']:
        """Get all attacking creatures."""
        attackers = []
        for card in self.battlefield[self.active_player]:
            if hasattr(card, 'attacking') and card.attacking:
                attackers.append(card)
        return attackers

    def get_creatures(self, player: int) -> List['Card']:
        """Get all creatures for a player."""
        from .cards import Creature, CreatureLand
        creatures = []
        for card in self.battlefield[player]:
            if isinstance(card, Creature):
                creatures.append(card)
            elif isinstance(card, CreatureLand) and card.is_creature:
                creatures.append(card)
        return creatures

    def signature(self) -> tuple:
        """Create a hashable signature for memoization.

        Note: Turn number is NOT included because the game outcome depends only
        on the current position, not how many turns it took to get there.
        This greatly improves memoization cache hits.
        """
        p1_hand = tuple(sorted(c.name for c in self.hands[0]))
        p2_hand = tuple(sorted(c.name for c in self.hands[1]))
        # Include all combat-relevant state: attacking, damage, and creature attributes
        # Note: entered_this_turn only matters for summoning sickness (attacking/tapping)
        p1_bf = tuple(sorted((c.name, c.tapped,
                              getattr(c, 'stun_counters', 0),
                              getattr(c, 'entered_this_turn', False),
                              getattr(c, 'is_creature', False),
                              getattr(c, 'attacking', False),
                              getattr(c, 'damage', 0),
                              getattr(c, 'plus_counters', 0),
                              getattr(c, 'return_to_hand', False),
                              getattr(c, 'level', 0),
                              getattr(c, 'storage_counters', 0),
                              getattr(c, 'stay_tapped', False),
                              getattr(c, 'depletion_counters', 0),
                              getattr(c, 'spore_counters', 0),
                              getattr(c, 'eot_power_boost', 0),
                              getattr(c, 'eot_toughness_boost', 0))
                             for c in self.battlefield[0]))
        p2_bf = tuple(sorted((c.name, c.tapped,
                              getattr(c, 'stun_counters', 0),
                              getattr(c, 'is_creature', False),
                              getattr(c, 'entered_this_turn', False),
                              getattr(c, 'attacking', False),
                              getattr(c, 'damage', 0),
                              getattr(c, 'plus_counters', 0),
                              getattr(c, 'return_to_hand', False),
                              getattr(c, 'level', 0),
                              getattr(c, 'storage_counters', 0),
                              getattr(c, 'stay_tapped', False),
                              getattr(c, 'depletion_counters', 0),
                              getattr(c, 'spore_counters', 0),
                              getattr(c, 'eot_power_boost', 0),
                              getattr(c, 'eot_toughness_boost', 0))
                             for c in self.battlefield[1]))
        p1_art = tuple(sorted((c.name, c.tapped) for c in self.artifacts[0]))
        p2_art = tuple(sorted((c.name, c.tapped) for c in self.artifacts[1]))
        # Include blocking assignments for combat phases
        blocking = tuple(sorted(self.blocking_assignments.items()))
        return (
            tuple(self.life),
            self.active_player,
            self.land_played_this_turn,
            p1_hand, p2_hand,
            p1_bf, p2_bf,
            p1_art, p2_art,
            blocking
        )

    def board_signature(self) -> tuple:
        """Create a signature excluding life totals for dominance checking.

        Two states with the same board_signature but different life totals
        can be compared for dominance: if state A has lower life for both
        players than state B, then A is dominated by B.
        """
        p1_hand = tuple(sorted(c.name for c in self.hands[0]))
        p2_hand = tuple(sorted(c.name for c in self.hands[1]))
        p1_bf = tuple(sorted((c.name, c.tapped,
                              getattr(c, 'stun_counters', 0),
                              getattr(c, 'entered_this_turn', False),
                              getattr(c, 'is_creature', False),
                              getattr(c, 'attacking', False),
                              getattr(c, 'damage', 0),
                              getattr(c, 'plus_counters', 0),
                              getattr(c, 'return_to_hand', False),
                              getattr(c, 'level', 0),
                              getattr(c, 'storage_counters', 0),
                              getattr(c, 'stay_tapped', False),
                              getattr(c, 'depletion_counters', 0),
                              getattr(c, 'spore_counters', 0),
                              getattr(c, 'eot_power_boost', 0),
                              getattr(c, 'eot_toughness_boost', 0))
                             for c in self.battlefield[0]))
        p2_bf = tuple(sorted((c.name, c.tapped,
                              getattr(c, 'stun_counters', 0),
                              getattr(c, 'is_creature', False),
                              getattr(c, 'entered_this_turn', False),
                              getattr(c, 'attacking', False),
                              getattr(c, 'damage', 0),
                              getattr(c, 'plus_counters', 0),
                              getattr(c, 'return_to_hand', False),
                              getattr(c, 'level', 0),
                              getattr(c, 'storage_counters', 0),
                              getattr(c, 'stay_tapped', False),
                              getattr(c, 'depletion_counters', 0),
                              getattr(c, 'spore_counters', 0),
                              getattr(c, 'eot_power_boost', 0),
                              getattr(c, 'eot_toughness_boost', 0))
                             for c in self.battlefield[1]))
        p1_art = tuple(sorted((c.name, c.tapped) for c in self.artifacts[0]))
        p2_art = tuple(sorted((c.name, c.tapped) for c in self.artifacts[1]))
        blocking = tuple(sorted(self.blocking_assignments.items()))
        return (
            self.active_player,
            self.land_played_this_turn,
            p1_hand, p2_hand,
            p1_bf, p2_bf,
            p1_art, p2_art,
            blocking
        )
