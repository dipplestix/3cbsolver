from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import hashlib
import itertools
import json
import math

from cards import Card, Permanent, empty_pool, make_card

@dataclass
class PlayerState:
    life: int = 20
    hand: List[Card] = field(default_factory=list)
    graveyard: List[Card] = field(default_factory=list)
    mana_pool: Dict[str, int] = field(default_factory=empty_pool)
    land_played_this_turn: bool = False

@dataclass
class GameState:
    players: Tuple[PlayerState, PlayerState]
    battlefield: List[Permanent] = field(default_factory=list)
    turn: int = 0
    step: str = "BEGIN"
    turn_number: int = 1
    max_turns: int = 30
    history: set = field(default_factory=set)

    def clone(self) -> "GameState":
        import copy
        return copy.deepcopy(self)

    def hashable(self) -> str:
        payload = {
            "life": [p.life for p in self.players],
            "hands": [[c.name for c in p.hand] for p in self.players],
            "gy": [[c.name for c in p.graveyard] for p in self.players],
            "mp": [self.players[0].mana_pool.copy(), self.players[1].mana_pool.copy()],
            "bf": [{
                "name": perm.card.name,
                "ctrl": perm.controller,
                "t": perm.tapped,
                "sick": perm.summoning_sick,
                "dmg": perm.damage
            } for perm in self.battlefield],
            "turn": self.turn, "step": self.step, "tnum": self.turn_number
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

def begin_turn(state: GameState) -> None:
    for perm in state.battlefield:
        if perm.controller == state.turn:
            perm.tapped = False
            perm.damage = 0
            perm.summoning_sick = False if perm.controller == state.turn and perm.card.is_creature() else perm.summoning_sick
    state.players[state.turn].land_played_this_turn = False
    state.step = "MAIN"

def available_mana_actions(state: GameState, player: int):
    actions = []
    for idx, perm in enumerate(state.battlefield):
        if perm.controller != player:
            continue
        for ability in perm.card.activated_abilities(state, player, idx):
            actions.append(("ACTIVATE_ABILITY", ability))
    return actions

def available_cast_actions(state: GameState, player: int):
    acts = []
    for c in state.players[player].hand:
        if c.is_land() and c.can_play(state, player):
            acts.append(("PLAY_CARD", c))
    for c in state.players[player].hand:
        if not c.is_land() and c.can_play(state, player):
            acts.append(("PLAY_CARD", c))
    return acts

def all_attack_subsets(creatures):
    idxs = list(range(len(creatures)))
    subsets = []
    for r in range(len(idxs)+1):
        for comb in itertools.combinations(idxs, r):
            subsets.append(list(comb))
    return subsets

def best_blocking_assignment(attackers, blockers):
    A = len(attackers); B = len(blockers)
    best = None
    for match in itertools.product([None] + list(range(B)), repeat=A):
        used = set(); ok = True
        for m in match:
            if m is not None:
                if m in used: ok=False; break
                used.add(m)
        if not ok: continue
        dmg_to_face = 0; my_losses = 0; opp_losses = 0
        for ai, att in enumerate(attackers):
            blk_idx = match[ai]
            if blk_idx is None:
                dmg_to_face += att.card.power
            else:
                blk = blockers[blk_idx]
                att_kills = att.card.power >= blk.card.toughness
                blk_kills = blk.card.power >= att.card.toughness
                if att_kills: opp_losses += 1
                if blk_kills: my_losses += 1
        score = (dmg_to_face, my_losses - opp_losses)
        if best is None or score < best[0]:
            best = (score, match)
    return list(best[1]) if best else [None]*A

def resolve_combat(state: GameState, attackers_idx):
    atk = [p for p in state.battlefield if p.controller == state.turn and p.card.is_creature() and not p.summoning_sick]
    defn = [p for p in state.battlefield if p.controller != state.turn and p.card.is_creature()]
    chosen_attackers = [atk[i] for i in attackers_idx]
    block_assign = best_blocking_assignment(chosen_attackers, defn)
    to_destroy = set()
    for ai, att in enumerate(chosen_attackers):
        blk_idx = block_assign[ai]
        if blk_idx is None:
            state.players[1 - state.turn].life -= att.card.power
        else:
            blk = defn[blk_idx]
            if att.card.power >= blk.card.toughness:
                to_destroy.add(("def", blk_idx))
            if blk.card.power >= att.card.toughness:
                to_destroy.add(("atk", ai))
    for tag, idx in to_destroy:
        perm = chosen_attackers[idx] if tag=="atk" else defn[idx]
        if perm in state.battlefield:
            state.battlefield.remove(perm)
            state.players[perm.controller].graveyard.append(perm.card)

def outcome(state: GameState, perspective: int) -> Optional[int]:
    if state.players[1 - perspective].life <= 0 and state.players[perspective].life > 0:
        return +1
    if state.players[perspective].life <= 0 and state.players[1 - perspective].life > 0:
        return -1
    if state.players[0].life <= 0 and state.players[1].life <= 0:
        return 0
    return None

WIN, DRAW, LOSS = 1, 0, -1

def state_repetition_or_cap(state: GameState) -> bool:
    h = state.hashable()
    if h in state.history:
        return True
    state.history.add(h)
    if state.turn_number > state.max_turns:
        return True
    return False

def generate_main_phase_actions(state: GameState, player: int):
    acts = []
    acts.extend(available_mana_actions(state, player))
    acts.extend(available_cast_actions(state, player))
    acts.append(("PASS_MAIN", None))
    return acts

def do_action(state: GameState, player: int, action):
    kind, payload = action
    if kind == "ACTIVATE_ABILITY":
        payload.resolve(state, player)
    elif kind == "PLAY_CARD":
        payload.play(state, player)
    elif kind == "PASS_MAIN":
        state.step = "COMBAT_DECLARE"
    elif kind == "DECLARE_ATTACKERS":
        resolve_combat(state, payload)
        state.step = "END"
    elif kind == "PASS_COMBAT":
        state.step = "END"
    else:
        raise ValueError(f"Unknown action {kind}")

def generate_combat_actions(state: GameState, player: int):
    atk = [p for p in state.battlefield if p.controller == player and p.card.is_creature() and not p.summoning_sick]
    actions = []
    for subset in all_attack_subsets(atk):
        actions.append(("DECLARE_ATTACKERS", subset))
    actions.append(("PASS_COMBAT", None))
    return actions

def end_step_and_pass_turn(state: GameState) -> None:
    state.players[state.turn].mana_pool = empty_pool()
    state.turn = 1 - state.turn
    state.turn_number += 1
    state.step = "BEGIN"

def minimax(state: GameState, perspective: int, depth: int, alpha: int, beta: int) -> int:
    term = outcome(state, perspective)
    if term is not None:
        return 1 if term > 0 else (-1 if term < 0 else 0)
    if depth == 0 or state_repetition_or_cap(state):
        return 0
    player = state.turn
    maximizing = (player == perspective)
    if state.step == "BEGIN":
        begin_turn(state)
        return minimax(state, perspective, depth, alpha, beta)
    if state.step == "MAIN":
        actions = generate_main_phase_actions(state, player)
        best_val = -math.inf if maximizing else math.inf
        for a in actions:
            st2 = state.clone()
            do_action(st2, player, a)
            val = minimax(st2, perspective, depth-1, alpha, beta)
            if maximizing:
                best_val = max(best_val, val); alpha = max(alpha, val)
                if beta <= alpha: break
            else:
                best_val = min(best_val, val); beta = min(beta, val)
                if beta <= alpha: break
        return best_val
    if state.step == "COMBAT_DECLARE":
        actions = generate_combat_actions(state, player)
        best_val = -math.inf if maximizing else math.inf
        for a in actions:
            st2 = state.clone()
            do_action(st2, player, a)
            if st2.step == "END":
                end_step_and_pass_turn(st2)
            val = minimax(st2, perspective, depth-1, alpha, beta)
            if maximizing:
                best_val = max(best_val, val); alpha = max(alpha, val)
                if beta <= alpha: break
            else:
                best_val = min(best_val, val); beta = min(beta, val)
                if beta <= alpha: break
        return best_val
    if state.step == "END":
        st2 = state.clone()
        end_step_and_pass_turn(st2)
        return minimax(st2, perspective, depth-1, alpha, beta)
    return 0

def build_deck(card_names: List[str]) -> List[Card]:
    assert len(card_names) == 3, "3CB decks must have exactly 3 cards"
    return [make_card(n) for n in card_names]

def init_game(deckA: List[Card], deckB: List[Card], on_the_play: int, max_turns=30) -> "GameState":
    p0 = PlayerState(hand=[c for c in deckA], life=20)
    p1 = PlayerState(hand=[c for c in deckB], life=20)
    gs = GameState(players=(p0, p1), turn=on_the_play, turn_number=1, max_turns=max_turns)
    gs.step = "BEGIN"
    return gs

def play_game(deckA: List[Card], deckB: List[Card], on_the_play: int, search_depth=8, max_turns=30) -> int:
    state = init_game(deckA, deckB, on_the_play, max_turns=max_turns)
    res = minimax(state, perspective=on_the_play, depth=search_depth, alpha=-math.inf, beta=math.inf)
    return res

def play_match(deckA: List[Card], deckB: List[Card], search_depth=8, max_turns=30):
    WIN, DRAW, LOSS = 1, 0, -1
    stateA = build_deck([c.name if hasattr(c, "name") else c for c in deckA]) if isinstance(deckA[0], str) else deckA
    stateB = build_deck([c.name if hasattr(c, "name") else c for c in deckB]) if isinstance(deckB[0], str) else deckB
    g1 = play_game([c for c in stateA], [c for c in stateB], on_the_play=0, search_depth=search_depth, max_turns=max_turns)
    g2 = play_game([c for c in stateA], [c for c in stateB], on_the_play=1, search_depth=search_depth, max_turns=max_turns)
    score_map = {WIN: 1.0, DRAW: 0.5, LOSS: 0.0}
    a_score = score_map[g1] + (1.0 - score_map[g2])
    b_score = 2.0 - a_score
    return {"game1_A_on_play": g1, "game2_B_on_play": g2, "A_points": a_score, "B_points": b_score}

# Tiny helper for RR tourneys
def round_robin(decks: Dict[str, List[str]], search_depth=8, max_turns=20):
    names = list(decks.keys())
    n = len(names)
    points = {name: 0.0 for name in names}
    mat = [[None]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                mat[i][j] = "-"
                continue
            deckA = build_deck(decks[names[i]])
            deckB = build_deck(decks[names[j]])
            res = play_match(deckA, deckB, search_depth=search_depth, max_turns=max_turns)
            ptsA = res["A_points"]
            mat[i][j] = f"{ptsA:.1f}"
            points[names[i]] += ptsA
    import pandas as pd
    df = pd.DataFrame(mat, index=names, columns=names)
    totals = pd.Series(points)
    df["Total"] = totals
    return df
