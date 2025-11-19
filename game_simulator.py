"""Turn-based duel simulator between two pre-defined creatures."""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import inf
from typing import List, Optional, Sequence

from cards import Card, get_card

MAX_CONSECUTIVE_PASSES = 10


@dataclass(frozen=True)
class CreatureState:
    card: Optional[Card]
    tapped: bool = False

    def is_present(self) -> bool:
        return self.card is not None

    def tap(self) -> "CreatureState":
        if not self.card:
            return self
        return CreatureState(card=self.card, tapped=True)

    def untap(self) -> "CreatureState":
        if not self.card:
            return self
        return CreatureState(card=self.card, tapped=False)

    def remove(self) -> "CreatureState":
        return CreatureState(card=None, tapped=False)


@dataclass(frozen=True)
class GameState:
    life_totals: Sequence[int]
    creatures: Sequence[CreatureState]
    active_player: int
    stage: str  # "action" or "block"
    passes_in_row: int
    pending_attack_from: Optional[int] = None

    def current_actor(self) -> int:
        if self.stage == "action":
            return self.active_player
        if self.stage == "block" and self.pending_attack_from is not None:
            return 1 - self.pending_attack_from
        raise ValueError("Invalid game stage")

    def is_terminal(self) -> bool:
        return (
            self.life_totals[0] <= 0
            or self.life_totals[1] <= 0
            or self.passes_in_row >= MAX_CONSECUTIVE_PASSES
        )

    def evaluate(self) -> float:
        if self.life_totals[0] <= 0 < self.life_totals[1]:
            return -inf
        if self.life_totals[1] <= 0 < self.life_totals[0]:
            return inf
        if self.passes_in_row >= MAX_CONSECUTIVE_PASSES:
            return 0.0
        score = float(self.life_totals[0] - self.life_totals[1])
        if self.creatures[0].card and not self.creatures[1].card:
            score += 5.0
        if self.creatures[1].card and not self.creatures[0].card:
            score -= 5.0
        return score

    def legal_moves(self) -> List[str]:
        if self.stage == "action":
            moves = ["pass"]
            creature = self.creatures[self.active_player]
            if creature.card and not creature.tapped:
                moves.append("attack")
            return moves

        if self.stage == "block":
            defender = 1 - self.pending_attack_from
            defender_creature = self.creatures[defender]
            moves = ["no_block"]
            if defender_creature.card and not defender_creature.tapped:
                moves.insert(0, "block")
            return moves

        raise ValueError(f"Unknown stage {self.stage}")

    def transition(self, move: str) -> "GameState":
        if self.stage == "action":
            if move == "pass":
                next_player = 1 - self.active_player
                return replace(
                    self,
                    active_player=next_player,
                    stage="action",
                    passes_in_row=self.passes_in_row + 1,
                    creatures=_untap_for_player(self.creatures, next_player),
                    pending_attack_from=None,
                )
            if move == "attack":
                attacker = self.active_player
                creatures = _update_creature(
                    self.creatures,
                    attacker,
                    self.creatures[attacker].tap(),
                )
                return replace(
                    self,
                    creatures=creatures,
                    stage="block",
                    passes_in_row=0,
                    pending_attack_from=attacker,
                )
            raise ValueError(f"Illegal move {move} in action stage")

        if self.stage == "block":
            attacker = self.pending_attack_from
            if attacker is None:
                raise ValueError("Block stage without attacker")
            defender = 1 - attacker
            creatures = self.creatures
            life = list(self.life_totals)
            if move == "no_block":
                damage = creatures[attacker].card.power if creatures[attacker].card else 0
                life[defender] -= damage
            elif move == "block":
                creatures = _resolve_block(combatants=creatures, attacker=attacker, defender=defender)
            else:
                raise ValueError(f"Illegal block move {move}")

            next_player = defender
            return replace(
                self,
                life_totals=tuple(life),
                creatures=_untap_for_player(creatures, next_player),
                active_player=next_player,
                stage="action",
                passes_in_row=0,
                pending_attack_from=None,
            )

        raise ValueError(f"Unknown stage {self.stage}")


@dataclass
class GameTreeNode:
    state: GameState
    move: Optional[str] = None
    children: List["GameTreeNode"] = None
    is_repetition_draw: bool = False

    def __post_init__(self) -> None:
        if self.children is None:
            self.children = []


def _update_creature(creatures: Sequence[CreatureState], index: int, new_creature: CreatureState) -> Sequence[CreatureState]:
    updated = list(creatures)
    updated[index] = new_creature
    return tuple(updated)


def _untap_for_player(creatures: Sequence[CreatureState], player: int) -> Sequence[CreatureState]:
    if player not in (0, 1):
        return creatures
    updated = list(creatures)
    updated[player] = updated[player].untap()
    return tuple(updated)


def _resolve_block(combatants: Sequence[CreatureState], attacker: int, defender: int) -> Sequence[CreatureState]:
    updated = list(combatants)
    atk = combatants[attacker]
    dfn = combatants[defender]
    if not atk.card or not dfn.card:
        return tuple(updated)

    atk_damage = dfn.card.power
    def_damage = atk.card.power
    if atk_damage >= atk.card.toughness:
        updated[attacker] = atk.remove()
    if def_damage >= dfn.card.toughness:
        updated[defender] = dfn.remove()
    return tuple(updated)


def build_game_tree(
    state: GameState,
    path: Optional[List[GameState]] = None,
    cache: Optional[dict[GameState, GameTreeNode]] = None,
) -> GameTreeNode:
    if path is None:
        path = []
    if cache is None:
        cache = {}

    if state in path:
        return GameTreeNode(state=state, is_repetition_draw=True)

    if state in cache:
        return cache[state]

    node = GameTreeNode(state=state)
    cache[state] = node
    if state.is_terminal():
        return node

    path.append(state)
    for move in state.legal_moves():
        child_state = state.transition(move)
        child_node = build_game_tree(child_state, path, cache)
        child_node.move = move
        node.children.append(child_node)
    path.pop()
    return node


def alpha_beta(node: GameTreeNode, alpha: float = -inf, beta: float = inf) -> float:
    if node.state.is_terminal():
        return node.state.evaluate()
    if node.is_repetition_draw:
        return 0.0

    maximizing = node.state.current_actor() == 0
    if maximizing:
        value = -inf
        for child in node.children:
            value = max(value, alpha_beta(child, alpha, beta))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value

    value = inf
    for child in node.children:
        value = min(value, alpha_beta(child, alpha, beta))
        beta = min(beta, value)
        if beta <= alpha:
            break
    return value


def setup_duel(attacker_name: str, defender_name: str, life_total: int = 20) -> GameState:
    card_a = get_card(attacker_name)
    card_b = get_card(defender_name)
    creatures = (
        CreatureState(card=card_a, tapped=False),
        CreatureState(card=card_b, tapped=False),
    )
    return GameState(
        life_totals=(life_total, life_total),
        creatures=creatures,
        active_player=0,
        stage="action",
        passes_in_row=0,
    )


def main() -> None:
    initial = setup_duel("Shivan Dragon", "Savannah Lions", life_total=20)
    root = build_game_tree(initial)
    score = alpha_beta(root)
    print("Alpha-beta evaluation (player 0 perspective):", score)


if __name__ == "__main__":
    main()
