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
        return card.get_mana_output()

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
        """Pay mana of a specific color, using card-driven mana production. Returns new state."""
        ns = self.copy()
        remaining = amount

        # Get lands of the right color that can produce mana
        lands = [c for c in ns.battlefield[player]
                 if hasattr(c, 'mana_produced') and c.mana_produced == color and not c.tapped]

        to_sacrifice = []
        for card in lands:
            if remaining <= 0:
                break

            # Skip creature lands with summoning sickness
            if card.is_creature() and getattr(card, 'entered_this_turn', False):
                continue

            # Use card-driven mana production
            mana_produced = card.tap_for_mana()
            remaining -= mana_produced

            # Check if card should be sacrificed after tapping
            if card.should_sacrifice_after_tap():
                to_sacrifice.append(card)

        # Handle sacrifices
        for card in to_sacrifice:
            ns.battlefield[player].remove(card)
            ns.graveyard[player].append(card)

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
        return [card for card in self.battlefield[player] if card.is_creature()]

    def signature(self) -> tuple:
        """Create a hashable signature for memoization.

        Note: Turn number is NOT included because the game outcome depends only
        on the current position, not how many turns it took to get there.
        This greatly improves memoization cache hits.

        Each card provides its own signature state via get_signature_state(),
        making the system extensible without modifying GameState.
        """
        p1_hand = tuple(sorted(c.name for c in self.hands[0]))
        p2_hand = tuple(sorted(c.name for c in self.hands[1]))
        # Each card knows what state it needs to include
        p1_bf = tuple(sorted(c.get_signature_state() for c in self.battlefield[0]))
        p2_bf = tuple(sorted(c.get_signature_state() for c in self.battlefield[1]))
        p1_art = tuple(sorted(c.get_signature_state() for c in self.artifacts[0]))
        p2_art = tuple(sorted(c.get_signature_state() for c in self.artifacts[1]))
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

        Uses card-driven get_signature_state() for extensibility.
        """
        p1_hand = tuple(sorted(c.name for c in self.hands[0]))
        p2_hand = tuple(sorted(c.name for c in self.hands[1]))
        p1_bf = tuple(sorted(c.get_signature_state() for c in self.battlefield[0]))
        p2_bf = tuple(sorted(c.get_signature_state() for c in self.battlefield[1]))
        p1_art = tuple(sorted(c.get_signature_state() for c in self.artifacts[0]))
        p2_art = tuple(sorted(c.get_signature_state() for c in self.artifacts[1]))
        blocking = tuple(sorted(self.blocking_assignments.items()))
        return (
            self.active_player,
            self.land_played_this_turn,
            p1_hand, p2_hand,
            p1_bf, p2_bf,
            p1_art, p2_art,
            blocking
        )
