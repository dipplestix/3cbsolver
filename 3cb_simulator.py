from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import itertools, math, hashlib, json

COLORS = ["W", "U", "B", "R", "G"]
ALL_MANA_SYMBOLS = COLORS + ["C"]

def parse_mana_cost(cost: str) -> Dict[str, int]:
    result = {c: 0 for c in ALL_MANA_SYMBOLS}
    result["generic"] = 0
    i = 0
    while i < len(cost):
        ch = cost[i]
        if ch.isdigit():
            j = i
            while j < len(cost) and cost[j].isdigit():
                j += 1
            result["generic"] += int(cost[i:j])
            i = j
        else:
            if ch in ALL_MANA_SYMBOLS:
                result[ch] += 1
                i += 1
            else:
                raise ValueError(f"Unsupported mana symbol in cost: {ch}")
    return result

def can_pay(cost: Dict[str, int], pool: Dict[str, int]) -> bool:
    for c in COLORS + ["C"]:
        if pool.get(c, 0) < cost.get(c, 0):
            return False
    excess = sum(pool.get(k, 0) - cost.get(k, 0) for k in ALL_MANA_SYMBOLS)
    return excess >= cost.get("generic", 0)

def pay(cost: Dict[str, int], pool: Dict[str, int]) -> Dict[str, int]:
    pool = pool.copy()
    for c in COLORS + ["C"]:
        need = cost.get(c, 0)
        if need:
            assert pool.get(c, 0) >= need
            pool[c] -= need
    generic = cost.get("generic", 0)
    if generic:
        for k in ["C"] + COLORS:
            use = min(pool.get(k, 0), generic)
            pool[k] -= use
            generic -= use
            if generic == 0:
                break
        assert generic == 0
    return pool

def empty_pool() -> Dict[str, int]:
    return {k: 0 for k in ALL_MANA_SYMBOLS}

@dataclass
class Card:
    name: str
    types: Tuple[str, ...]
    cost_str: str = ""
    haste: bool = False
    power: int = 0
    toughness: int = 0

    def mana_cost(self) -> Dict[str, int]:
        return parse_mana_cost(self.cost_str) if self.cost_str else {"generic": 0, **{k:0 for k in ALL_MANA_SYMBOLS}}

    def can_play(self, state: "GameState", player: int) -> bool:
        if self.is_land():
            return (not state.players[player].land_played_this_turn)
        else:
            return can_pay(self.mana_cost(), state.players[player].mana_pool)

    def play(self, state: "GameState", player: int) -> None:
        if self.is_land():
            state.players[player].land_played_this_turn = True
            state.battlefield.append(Permanent(card=self, controller=player))
            state.players[player].hand.remove(self)
        elif self.is_creature():
            state.players[player].mana_pool = pay(self.mana_cost(), state.players[player].mana_pool)
            perm = Permanent(card=self, controller=player, summoning_sick=(not self.haste))
            state.battlefield.append(perm)
            state.players[player].hand.remove(self)
        else:
            state.players[player].mana_pool = pay(self.mana_cost(), state.players[player].mana_pool)
            self.resolve_noncreature(state, player)
            state.players[player].hand.remove(self)
            state.players[player].graveyard.append(self)

    def resolve_noncreature(self, state: "GameState", player: int) -> None:
        pass

    def state_static(self, state: "GameState", me: int) -> None:
        pass

    def is_land(self) -> bool:
        return "Land" in self.types

    def is_creature(self) -> bool:
        return "Creature" in self.types

    def is_artifact(self) -> bool:
        return "Artifact" in self.types

@dataclass
class Permanent:
    card: Card
    controller: int
    tapped: bool = False
    summoning_sick: bool = False
    damage: int = 0

    def can_attack(self) -> bool:
        return self.card.is_creature() and (not self.summoning_sick)

class BasicLand(Card):
    def __init__(self, name: str, color: Optional[str] = None):
        types = ("Land",)
        super().__init__(name=name, types=types)
        self._color = color

    def activate_tap_for_mana(self, state: "GameState", player: int) -> bool:
        for perm in state.battlefield:
            if perm.card is self and perm.controller == player and not perm.tapped:
                perm.tapped = True
                if self._color:
                    state.players[player].mana_pool[self._color] += 1
                else:
                    state.players[player].mana_pool["C"] += 1
                return True
        return False

class BlackLotus(Card):
    def __init__(self):
        super().__init__(name="Black Lotus", types=("Artifact",), cost_str="0")

    def can_play(self, state, player):
        return True

    def play(self, state, player):
        state.players[player].hand.remove(self)
        state.battlefield.append(Permanent(card=self, controller=player))

    def sac_for_mana(self, state: "GameState", player: int, color: str) -> bool:
        for i, perm in enumerate(state.battlefield):
            if perm.card is self and perm.controller == player:
                state.battlefield.pop(i)
                state.players[player].graveyard.append(self)
                if color not in COLORS:
                    raise ValueError("Black Lotus can only add colored mana (W/U/B/R/G)")
                state.players[player].mana_pool[color] += 3
                return True
        return False

class LotusPetal(Card):
    def __init__(self):
        super().__init__(name="Lotus Petal", types=("Artifact",), cost_str="0")

    def can_play(self, state, player):
        return True

    def play(self, state, player):
        state.players[player].hand.remove(self)
        state.battlefield.append(Permanent(card=self, controller=player))

    def sac_for_mana(self, state: "GameState", player: int, color: str) -> bool:
        for i, perm in enumerate(state.battlefield):
            if perm.card is self and perm.controller == player:
                state.battlefield.pop(i)
                state.players[player].graveyard.append(self)
                if color not in ALL_MANA_SYMBOLS:
                    raise ValueError("Lotus Petal can add W/U/B/R/G/C")
                state.players[player].mana_pool[color] += 1
                return True
        return False

class SimpleCreature(Card):
    def __init__(self, name: str, cost: str, power: int, toughness: int, haste: bool=False):
        super().__init__(name=name, types=("Creature",), cost_str=cost, power=power, toughness=toughness, haste=haste)

class LightningBolt(Card):
    def __init__(self):
        super().__init__(name="Lightning Bolt", types=("Sorcery",), cost_str="R")

    def resolve_noncreature(self, state: "GameState", player: int) -> None:
        opponent = 1 - player
        if state.players[opponent].life <= 3:
            state.players[opponent].life -= 3
            return
        opp_creatures = [p for p in state.battlefield if p.controller == opponent and p.card.is_creature()]
        if opp_creatures:
            target = max(opp_creatures, key=lambda p: (p.card.power, p.card.toughness))
            target.damage += 3
            if target.damage >= target.card.toughness:
                state.battlefield.remove(target)
                state.players[opponent].graveyard.append(target.card)
        else:
            state.players[opponent].life -= 3

@dataclass
class PlayerState:
    life: int = 20
    hand: List[Card] = field(default_factory=list)
    graveyard: List[Card] = field(default_factory=list)
    mana_pool: Dict[str, int] = field(default_factory=lambda: {k:0 for k in ALL_MANA_SYMBOLS})
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
    for perm in state.battlefield:
        if perm.controller == player and not perm.tapped and isinstance(perm.card, BasicLand):
            actions.append(("TAP_LAND", perm.card))
    for perm in state.battlefield:
        if perm.controller == player and isinstance(perm.card, (BlackLotus, LotusPetal)):
            for col in ALL_MANA_SYMBOLS if isinstance(perm.card, LotusPetal) else COLORS:
                actions.append(("SAC_FOR_MANA", (perm.card, col)))
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
    if kind == "TAP_LAND":
        payload.activate_tap_for_mana(state, player)
    elif kind == "SAC_FOR_MANA":
        card, color = payload
        if isinstance(card, BlackLotus):
            card.sac_for_mana(state, player, color)
        elif isinstance(card, LotusPetal):
            card.sac_for_mana(state, player, color)
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

def make_card(name: str) -> Card:
    name = name.strip().lower()
    if name in ["plains", "island", "swamp", "mountain", "forest", "wastes"]:
        color = {"plains":"W", "island":"U", "swamp":"B", "mountain":"R", "forest":"G", "wastes":None}[name]
        return BasicLand(name=name.title(), color=color)
    if name == "black lotus":
        return BlackLotus()
    if name == "lotus petal":
        return LotusPetal()
    if name == "grizzly bears":
        return SimpleCreature("Grizzly Bears", cost="1G", power=2, toughness=2)
    if name == "elite vanguard":
        return SimpleCreature("Elite Vanguard", cost="W", power=2, toughness=1)
    if name == "savannah lions":
        return SimpleCreature("Savannah Lions", cost="W", power=2, toughness=1)
    if name == "lightning bolt":
        return LightningBolt()
    return SimpleCreature(name.title(), cost="2", power=2, toughness=2)

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
