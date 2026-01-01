"""
Solver for the 3CB simulator.
Takes any two hands and finds optimal play using minimax.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from copy import deepcopy

from .cards import Card, Creature, Land, CreatureLand, Artifact, Action


@dataclass
class GameState:
    """Represents the complete state of a game."""

    life: List[int] = field(default_factory=lambda: [20, 20])
    hands: List[List[Card]] = field(default_factory=lambda: [[], []])
    battlefield: List[List[Card]] = field(default_factory=lambda: [[], []])
    artifacts: List[List[Card]] = field(default_factory=lambda: [[], []])
    graveyard: List[List[Card]] = field(default_factory=lambda: [[], []])

    active_player: int = 0
    phase: str = "main1"  # main1, combat_attack, combat_block, combat_damage
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

    def get_attackers(self) -> List[Card]:
        """Get all attacking creatures."""
        attackers = []
        for card in self.battlefield[self.active_player]:
            if hasattr(card, 'attacking') and card.attacking:
                attackers.append(card)
        return attackers

    def get_creatures(self, player: int) -> List[Card]:
        """Get all creatures for a player."""
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


def get_available_actions(state: GameState) -> List[Action]:
    """Get all available actions for the current player and phase."""
    actions = []
    player = state.active_player

    if state.phase == "main1":
        # Collect play actions from hand
        for card in state.hands[player]:
            actions.extend(card.get_play_actions(state))

        # Collect battlefield actions (activated abilities)
        for card in state.battlefield[player]:
            actions.extend(card.get_battlefield_actions(state))

        # Always can pass to combat
        def pass_to_combat(s: GameState) -> GameState:
            ns = s.copy()
            ns.phase = "combat_attack"
            return ns
        actions.append(Action("Pass to Combat", pass_to_combat))

    elif state.phase == "combat_attack":
        # Collect battlefield actions for active player (e.g., Luminarch Aspirant trigger)
        for card in state.battlefield[player]:
            actions.extend(card.get_battlefield_actions(state))

        # Collect attack actions, deduplicating identical creatures
        # Only generate one "Attack with X" action per creature type to avoid
        # exploring equivalent permutations (e.g., "Sap1 attacks then Sap2" vs "Sap2 then Sap1")
        seen_attackers = set()
        for i, card in enumerate(state.battlefield[player]):
            if isinstance(card, Creature) or isinstance(card, CreatureLand):
                # Check if this creature can attack
                if hasattr(card, 'can_attack') and not card.can_attack():
                    continue
                if card.tapped:
                    continue
                if getattr(card, 'attacking', False):
                    continue
                if getattr(card, 'entered_this_turn', False):
                    continue

                # Create a signature for this creature type
                creature_sig = (card.name, getattr(card, 'power', 0), getattr(card, 'toughness', 0),
                                getattr(card, 'plus_counters', 0), getattr(card, 'level', 0))
                if creature_sig in seen_attackers:
                    continue  # Skip duplicate creature types
                seen_attackers.add(creature_sig)

                # Generate attack action that picks this specific creature
                def make_attack(card_idx):
                    def attack(s: GameState) -> GameState:
                        ns = s.copy()
                        attacker = ns.battlefield[player][card_idx]
                        attacker.attacking = True
                        attacker.tapped = True
                        return ns
                    return attack
                actions.append(Action(f"Attack with {card.name}", make_attack(i)))

        # Always can choose not to attack
        def no_attack(s: GameState) -> GameState:
            ns = s.copy()
            # Check if any attackers
            if ns.get_attackers():
                ns.phase = "combat_block"
            else:
                ns.phase = "end_turn"
            return ns
        actions.append(Action("No Attack", no_attack))

    elif state.phase == "combat_block":
        # Defending player chooses blocks
        defender = 1 - player

        # Build attackers list with battlefield indices
        attackers_with_idx = []
        for i, card in enumerate(state.battlefield[state.active_player]):
            if hasattr(card, 'attacking') and card.attacking:
                attackers_with_idx.append((i, card))

        # Collect battlefield actions for defender (e.g., activate Mutavault to block)
        for card in state.battlefield[defender]:
            actions.extend(card.get_battlefield_actions(state))

        # Collect block actions, deduplicating identical blocker/attacker combinations
        # This avoids exploring equivalent permutations
        seen_blocks = set()  # (blocker_sig, attacker_sig)
        blocked_attackers = set(state.blocking_assignments.keys())
        assigned_blockers = set(state.blocking_assignments.values())

        for blocker_idx, blocker in enumerate(state.battlefield[defender]):
            if not (isinstance(blocker, Creature) or isinstance(blocker, CreatureLand)):
                continue
            if blocker.tapped:
                continue
            if blocker_idx in assigned_blockers:
                continue  # Already blocking

            # Check if creature (CreatureLand needs is_creature check)
            if isinstance(blocker, CreatureLand) and not blocker.is_creature:
                continue

            blocker_sig = (blocker.name, getattr(blocker, 'power', 0), getattr(blocker, 'toughness', 0),
                           getattr(blocker, 'plus_counters', 0))

            for att_idx, attacker in attackers_with_idx:
                if att_idx in blocked_attackers:
                    continue  # Already blocked

                # Check if can block
                if hasattr(blocker, 'can_block') and not blocker.can_block(attacker):
                    continue

                attacker_sig = (attacker.name, getattr(attacker, 'power', 0))
                block_sig = (blocker_sig, attacker_sig)

                if block_sig in seen_blocks:
                    continue  # Skip duplicate blocker/attacker combination
                seen_blocks.add(block_sig)

                # Generate block action
                def make_block(b_idx, a_idx):
                    def block(s: GameState) -> GameState:
                        ns = s.copy()
                        ns.blocking_assignments[a_idx] = b_idx
                        return ns
                    return block
                actions.append(Action(f"Block {attacker.name} with {blocker.name}",
                                      make_block(blocker_idx, att_idx)))

        # Always can choose not to block (proceeds to combat damage)
        def no_block(s: GameState) -> GameState:
            ns = s.copy()
            ns.phase = "combat_damage"
            return ns
        actions.append(Action("No Block", no_block))

    return actions


def get_creature_power(card) -> int:
    """Get a creature's current power (including +1/+1 counters, levels, eot boosts, etc)."""
    if hasattr(card, 'current_power'):
        base = card.current_power
    else:
        base = card.power if hasattr(card, 'power') else 0
    return base + getattr(card, 'eot_power_boost', 0)


def get_creature_toughness(card) -> int:
    """Get a creature's current toughness (including +1/+1 counters, levels, eot boosts, etc)."""
    if hasattr(card, 'current_toughness'):
        base = card.current_toughness
    else:
        base = card.toughness if hasattr(card, 'toughness') else 0
    return base + getattr(card, 'eot_toughness_boost', 0)


def has_first_strike(card) -> bool:
    """Check if creature has first strike."""
    if hasattr(card, 'has_first_strike'):
        return card.has_first_strike
    if hasattr(card, 'keywords'):
        return 'first_strike' in card.keywords
    return False


def has_double_strike(card) -> bool:
    """Check if creature has double strike."""
    if hasattr(card, 'has_double_strike'):
        return card.has_double_strike
    if hasattr(card, 'keywords'):
        return 'double_strike' in card.keywords
    return False


def has_deathtouch(card) -> bool:
    """Check if creature has deathtouch."""
    if hasattr(card, 'has_deathtouch'):
        return card.has_deathtouch
    if hasattr(card, 'keywords'):
        return 'deathtouch' in card.keywords
    return False


def is_lethal_damage(damage: int, toughness: int, attacker_has_deathtouch: bool) -> bool:
    """Check if damage is lethal (considering deathtouch)."""
    if attacker_has_deathtouch and damage > 0:
        return True
    return damage >= toughness


def resolve_combat_damage(state: GameState) -> GameState:
    """Resolve combat damage with first strike and double strike support."""
    ns = state.copy()
    defender = 1 - ns.active_player

    # Build attacker list with indices for blocking lookup
    attackers_with_idx = []
    for i, card in enumerate(ns.battlefield[ns.active_player]):
        if hasattr(card, 'attacking') and card.attacking:
            attackers_with_idx.append((i, card))

    # Check if any creature has first strike or double strike
    any_first_strike = False
    for att_idx, attacker in attackers_with_idx:
        if has_first_strike(attacker) or has_double_strike(attacker):
            any_first_strike = True
            break
        blocker_idx = ns.blocking_assignments.get(att_idx)
        if blocker_idx is not None and blocker_idx < len(ns.battlefield[defender]):
            blocker = ns.battlefield[defender][blocker_idx]
            if has_first_strike(blocker) or has_double_strike(blocker):
                any_first_strike = True
                break

    # Track which creatures die (by battlefield index) to remove them later
    dead_attackers = set()  # indices in active_player's battlefield
    dead_blockers = set()   # indices in defender's battlefield

    # First strike damage step (if applicable)
    if any_first_strike:
        for att_idx, attacker in attackers_with_idx:
            if att_idx in dead_attackers:
                continue
            attacker_has_fs = has_first_strike(attacker) or has_double_strike(attacker)
            blocker_idx = ns.blocking_assignments.get(att_idx)

            if blocker_idx is not None and blocker_idx < len(ns.battlefield[defender]) and blocker_idx not in dead_blockers:
                blocker = ns.battlefield[defender][blocker_idx]
                blocker_has_fs = has_first_strike(blocker) or has_double_strike(blocker)
                attacker_has_dt = has_deathtouch(attacker)
                blocker_has_dt = has_deathtouch(blocker)

                # First strikers deal damage first
                if attacker_has_fs:
                    blocker.damage += get_creature_power(attacker)
                if blocker_has_fs:
                    attacker.damage += get_creature_power(blocker)

                # Check for deaths after first strike (considering deathtouch)
                attacker_toughness = get_creature_toughness(attacker)
                blocker_toughness = get_creature_toughness(blocker)

                if is_lethal_damage(blocker.damage, blocker_toughness, attacker_has_dt):
                    dead_blockers.add(blocker_idx)
                if is_lethal_damage(attacker.damage, attacker_toughness, blocker_has_dt):
                    dead_attackers.add(att_idx)
            else:
                # Unblocked with first strike - deal damage to player
                if attacker_has_fs:
                    damage = get_creature_power(attacker)
                    ns.life[defender] -= damage
                    if hasattr(attacker, 'on_deal_combat_damage_to_player'):
                        ns = attacker.on_deal_combat_damage_to_player(ns)

    # Regular damage step
    for att_idx, attacker in attackers_with_idx:
        if att_idx in dead_attackers:
            continue
        attacker_has_fs = has_first_strike(attacker)
        attacker_has_ds = has_double_strike(attacker)
        blocker_idx = ns.blocking_assignments.get(att_idx)

        if blocker_idx is not None and blocker_idx < len(ns.battlefield[defender]) and blocker_idx not in dead_blockers:
            blocker = ns.battlefield[defender][blocker_idx]
            blocker_has_fs = has_first_strike(blocker)
            blocker_has_ds = has_double_strike(blocker)
            attacker_has_dt = has_deathtouch(attacker)
            blocker_has_dt = has_deathtouch(blocker)

            # Non-first-strikers and double-strikers deal damage now
            if not attacker_has_fs or attacker_has_ds:
                blocker.damage += get_creature_power(attacker)
            if not blocker_has_fs or blocker_has_ds:
                attacker.damage += get_creature_power(blocker)

            # Check for deaths (considering deathtouch)
            attacker_toughness = get_creature_toughness(attacker)
            blocker_toughness = get_creature_toughness(blocker)

            if is_lethal_damage(attacker.damage, attacker_toughness, blocker_has_dt):
                dead_attackers.add(att_idx)
            if is_lethal_damage(blocker.damage, blocker_toughness, attacker_has_dt):
                dead_blockers.add(blocker_idx)
        else:
            # Unblocked - deal damage (double strikers deal again, non-FS deal now)
            if not attacker_has_fs or attacker_has_ds:
                damage = get_creature_power(attacker)
                ns.life[defender] -= damage
                if hasattr(attacker, 'on_deal_combat_damage_to_player'):
                    ns = attacker.on_deal_combat_damage_to_player(ns)

    # Remove dead creatures and trigger death abilities
    # Process in reverse index order to avoid index shifting issues
    for blocker_idx in sorted(dead_blockers, reverse=True):
        blocker = ns.battlefield[defender][blocker_idx]
        ns.graveyard[defender].append(blocker)
        if hasattr(blocker, 'on_death'):
            ns = blocker.on_death(ns)
        ns.battlefield[defender].pop(blocker_idx)

    for att_idx in sorted(dead_attackers, reverse=True):
        attacker = ns.battlefield[ns.active_player][att_idx]
        ns.graveyard[ns.active_player].append(attacker)
        if hasattr(attacker, 'on_death'):
            ns = attacker.on_death(ns)
        ns.battlefield[ns.active_player].pop(att_idx)

    # Check for game over
    if ns.life[0] <= 0:
        ns.game_over = True
        ns.winner = 1
    elif ns.life[1] <= 0:
        ns.game_over = True
        ns.winner = 0

    ns.phase = "end_turn"
    return ns


def end_turn(state: GameState) -> GameState:
    """Handle end of turn transitions."""
    ns = state.copy()

    # Reset combat state for active player
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'attacking'):
            card.attacking = False

    # Clear damage on ALL creatures (happens at end of each turn)
    for player in [0, 1]:
        for card in ns.battlefield[player]:
            if hasattr(card, 'damage'):
                card.damage = 0

    # Clear "until end of turn" effects
    for player in [0, 1]:
        for card in ns.battlefield[player]:
            if hasattr(card, 'eot_power_boost'):
                card.eot_power_boost = 0
            if hasattr(card, 'eot_toughness_boost'):
                card.eot_toughness_boost = 0

    # Call on_end_turn for creature lands (reset creature status)
    for card in ns.battlefield[ns.active_player]:
        if isinstance(card, CreatureLand):
            card.is_creature = False
            card.damage = 0
            card.attacking = False

    ns.blocking_assignments = {}

    # Switch to next player
    ns.active_player = 1 - ns.active_player
    ns.phase = "main1"
    ns.land_played_this_turn = False

    # Each player's turn increments the turn counter
    ns.turn += 1

    # Untap all permanents for the new active player
    # But stun counters replace untapping!
    # Also handle Undiscovered Paradise returning to hand
    cards_to_return = []
    for card in ns.battlefield[ns.active_player]:
        # Check for Undiscovered Paradise bounce
        if hasattr(card, 'return_to_hand') and card.return_to_hand:
            cards_to_return.append(card)
            continue
        if hasattr(card, 'stun_counters') and card.stun_counters > 0:
            # Stun counter replaces untap - remove counter, stay tapped
            card.stun_counters -= 1
        elif hasattr(card, 'stay_tapped') and card.stay_tapped:
            # Storage lands can choose to stay tapped
            pass
        else:
            card.tapped = False
        # Clear summoning sickness - permanents that were here at start of turn can attack
        if hasattr(card, 'entered_this_turn'):
            card.entered_this_turn = False
        # Reset Valiant trigger tracking
        if hasattr(card, 'targeted_this_turn'):
            card.targeted_this_turn = False
        # Reset Luminarch Aspirant combat trigger
        if hasattr(card, 'combat_trigger_used'):
            card.combat_trigger_used = False
    # Return bouncing lands to hand
    for card in cards_to_return:
        ns.battlefield[ns.active_player].remove(card)
        card.tapped = False
        card.return_to_hand = False
        ns.hands[ns.active_player].append(card)
    for card in ns.artifacts[ns.active_player]:
        card.tapped = False

    # Handle upkeep triggers (for cards that have them)
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'on_upkeep'):
            ns = card.on_upkeep(ns)

    # Auto-level creatures that should always level up (e.g., Student of Warfare)
    # This reduces branching by making level-up automatic when mana is available
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'auto_level') and card.auto_level:
            ns = card.do_auto_level(ns)

    return ns


def minimax(state: GameState, player: int, memo: Dict = None, depth: int = 0,
            alpha: int = -2, beta: int = 2, dominance: Dict = None) -> int:
    """
    Minimax search with alpha-beta pruning and transposition table.
    Returns: 1 = player wins, -1 = player loses, 0 = draw

    Memoization stores (value, flag) where flag is:
    - 'exact': This is the exact value
    - 'lower': This is a lower bound (alpha cutoff occurred)
    - 'upper': This is an upper bound (beta cutoff occurred)

    Dominance table maps board_signature -> list of (life, result) pairs.
    If a state with better life (for player) has result -1, any worse state is also -1.
    """
    if memo is None:
        memo = {}
    if dominance is None:
        dominance = {}

    # Terminal conditions
    if state.game_over:
        if state.winner == player:
            return 1
        elif state.winner == 1 - player:
            return -1
        return 0

    # Depth limit / repetition check - apply heuristics at max depth
    if depth > 500:
        # Only apply heuristics when hands are empty (game is in grinding phase)
        if not state.hands[0] and not state.hands[1]:
            p1_creatures = [c for c in state.battlefield[0] if hasattr(c, 'power') and c.power > 0]
            p2_creatures = [c for c in state.battlefield[1] if hasattr(c, 'power') and c.power > 0]

            # Check if one side has creatures and the other has nothing
            if p1_creatures and not p2_creatures:
                return 1 if player == 0 else -1
            elif p2_creatures and not p1_creatures:
                return 1 if player == 1 else -1

            # Check for token generator vs static creature
            # Thallid beats creatures that can't grow or generate tokens
            def has_token_gen(bf):
                return any(c.name == 'Thallid' for c in bf)

            def can_grow(creatures):
                for c in creatures:
                    if hasattr(c, 'plus_counters'):  # Aspirant, landfall creatures
                        return True
                    if hasattr(c, 'level'):  # Student of Warfare
                        return True
                return False

            p1_token_gen = has_token_gen(state.battlefield[0])
            p2_token_gen = has_token_gen(state.battlefield[1])
            p1_grows = can_grow(p1_creatures)
            p2_grows = can_grow(p2_creatures)

            if p2_token_gen and not p1_token_gen and not p1_grows:
                return 1 if player == 1 else -1
            if p1_token_gen and not p2_token_gen and not p2_grows:
                return 1 if player == 0 else -1

        return 0  # Draw by excessive depth (stalemate)

    # Transposition table lookup
    key = (state.signature(), state.phase, player)
    if key in memo:
        cached_value, flag = memo[key]
        if flag == 'exact':
            return cached_value
        elif flag == 'lower' and cached_value >= beta:
            return cached_value  # Fail high
        elif flag == 'upper' and cached_value <= alpha:
            return cached_value  # Fail low

    # Dominance check: if a better state was a loss, this is also a loss
    board_key = (state.board_signature(), state.phase, player)
    if board_key in dominance:
        my_life = state.life[player]
        opp_life = state.life[1 - player]
        for (cached_my_life, cached_opp_life, cached_result) in dominance[board_key]:
            # If cached state had better/equal life for player and worse/equal for opponent
            # and resulted in a loss, then this state is also a loss
            if cached_my_life >= my_life and cached_opp_life <= opp_life:
                if cached_result == -1:
                    return -1  # Dominated by a losing state
            # If cached state had worse/equal life for player and better/equal for opponent
            # and resulted in a win, then this state is also a win
            if cached_my_life <= my_life and cached_opp_life >= opp_life:
                if cached_result == 1:
                    return 1  # Dominates a winning state

    original_alpha = alpha

    # Handle automatic phases
    if state.phase == "combat_damage":
        new_state = resolve_combat_damage(state)
        result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "end_turn":
        new_state = end_turn(state)
        result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        memo[key] = (result, 'exact')
        return result

    # Get available actions
    actions = get_available_actions(state)

    if not actions:
        # No actions available, pass
        if state.phase == "main1":
            new_state = state.copy()
            new_state.phase = "combat_attack"
            result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        elif state.phase == "combat_attack":
            new_state = state.copy()
            new_state.phase = "end_turn"
            result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        elif state.phase == "combat_block":
            new_state = state.copy()
            new_state.phase = "combat_damage"
            result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        else:
            result = 0
        memo[key] = (result, 'exact')
        return result

    # Determine who is making the decision
    # In main1 and combat_attack: active player decides
    # In combat_block: defending player (1 - active_player) decides
    if state.phase == "combat_block":
        decision_maker = 1 - state.active_player
    else:
        decision_maker = state.active_player

    if decision_maker == player:
        # Maximizing player
        best_score = -2
        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break  # Beta cutoff
    else:
        # Minimizing player
        best_score = 2
        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
            best_score = min(best_score, score)
            beta = min(beta, score)
            if alpha >= beta:
                break  # Alpha cutoff

    # Store in transposition table with appropriate flag
    if best_score <= original_alpha:
        memo[key] = (best_score, 'upper')  # Failed low, this is an upper bound
    elif best_score >= beta:
        memo[key] = (best_score, 'lower')  # Failed high, this is a lower bound
    else:
        memo[key] = (best_score, 'exact')  # Exact value
        # Only store EXACT values in dominance table (not alpha-beta bounds)
        if board_key not in dominance:
            dominance[board_key] = []
        dominance[board_key].append((state.life[player], state.life[1 - player], best_score))

    return best_score


def solve(p1_hand: List[Card], p2_hand: List[Card], first_player: int = 0) -> Tuple[int, str]:
    """
    Solve a matchup given the starting hands.

    Args:
        p1_hand: Player 1's starting hand (list of Card objects)
        p2_hand: Player 2's starting hand (list of Card objects)
        first_player: Who goes first (0 = P1, 1 = P2)

    Returns:
        Tuple of (result, description)
        result: 1 = P1 wins, -1 = P1 loses, 0 = draw
        description: Human readable result
    """
    initial_state = GameState(
        life=[20, 20],
        hands=[[c.copy() for c in p1_hand], [c.copy() for c in p2_hand]],
        battlefield=[[], []],
        artifacts=[[], []],
        graveyard=[[], []],
        active_player=first_player,
        phase="main1",
        turn=1
    )

    result = minimax(initial_state, 0, {}, 0)

    if result == 1:
        return (1, "P1 Wins")
    elif result == -1:
        return (result, "P2 Wins")
    else:
        return (0, "Draw/Tie")


def find_optimal_line(state: GameState, player: int, memo: Dict = None, depth: int = 0) -> List[Tuple[str, GameState]]:
    """
    Find the optimal game line where both players play perfectly.
    Returns list of (action_description, resulting_state) tuples.
    """
    if memo is None:
        memo = {}

    path = []

    while not state.game_over and depth < 100:
        # Handle automatic phases
        if state.phase == "combat_damage":
            state = resolve_combat_damage(state)
            path.append(("Combat Damage", state.copy()))
            continue

        if state.phase == "end_turn":
            state = end_turn(state)
            path.append(("End Turn", state.copy()))
            continue

        # Get available actions
        actions = get_available_actions(state)

        if not actions:
            break

        # Determine decision maker
        if state.phase == "combat_block":
            decision_maker = 1 - state.active_player
        else:
            decision_maker = state.active_player

        # Find best action
        best_action = None
        best_score = None

        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, decision_maker, memo, depth)

            if best_score is None or score > best_score:
                best_score = score
                best_action = action

        if best_action:
            state = best_action.execute(state)
            path.append((best_action.description, state.copy()))
        else:
            break

        depth += 1

    return path
