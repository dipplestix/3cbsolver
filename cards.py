from __future__ import annotations

"""Card and mana primitives for the 3CB simulator."""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

COLORS: List[str] = ["W", "U", "B", "R", "G"]
ALL_MANA_SYMBOLS: List[str] = COLORS + ["C"]


def parse_mana_cost(cost: str) -> Dict[str, int]:
    """Parse a Magic-style mana string (e.g. ``"1RG"``) into a cost mapping."""

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
    """Return ``True`` when the provided mana pool can satisfy ``cost``."""

    for c in COLORS + ["C"]:
        if pool.get(c, 0) < cost.get(c, 0):
            return False
    excess = sum(pool.get(k, 0) - cost.get(k, 0) for k in ALL_MANA_SYMBOLS)
    return excess >= cost.get("generic", 0)


def pay(cost: Dict[str, int], pool: Dict[str, int]) -> Dict[str, int]:
    """Produce a new mana pool after spending ``cost`` from ``pool``."""

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


AbilityExecutor = Callable[["GameState", int, int], None]


@dataclass(frozen=True)
class CardAbility:
    """Representation of an activated ability available to a permanent."""

    description: str
    source_index: int
    executor: AbilityExecutor

    def resolve(self, state: "GameState", player: int) -> None:
        self.executor(state, player, self.source_index)


@dataclass
class Card:
    name: str
    types: Tuple[str, ...]
    cost_str: str = ""
    haste: bool = False
    power: int = 0
    toughness: int = 0

    def mana_cost(self) -> Dict[str, int]:
        if not self.cost_str:
            return {"generic": 0, **{k: 0 for k in ALL_MANA_SYMBOLS}}
        return parse_mana_cost(self.cost_str)

    def can_play(self, state: "GameState", player: int) -> bool:
        if self.is_land():
            return not state.players[player].land_played_this_turn
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

    def activated_abilities(self, state: "GameState", player: int, source_index: int) -> Sequence[CardAbility]:
        """Return activated abilities available for this card when on the battlefield."""

        return []

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
        super().__init__(name=name, types=("Land",))
        self._color = color

    def activated_abilities(self, state: "GameState", player: int, source_index: int) -> Sequence[CardAbility]:
        if state.battlefield[source_index].controller != player:
            return []
        permanent = state.battlefield[source_index]
        if permanent.tapped:
            return []

        mana_symbol = self._color or "C"

        def _tap_for_mana(st: "GameState", pl: int, idx: int) -> None:
            if idx >= len(st.battlefield):
                return
            perm = st.battlefield[idx]
            if perm.controller != pl or perm.tapped:
                return
            perm.tapped = True
            st.players[pl].mana_pool[mana_symbol] += 1

        label = f"Tap {self.name} for {mana_symbol}"
        return [CardAbility(description=label, source_index=source_index, executor=_tap_for_mana)]


class BlackLotus(Card):
    def __init__(self):
        super().__init__(name="Black Lotus", types=("Artifact",), cost_str="0")

    def can_play(self, state, player):
        return True

    def play(self, state, player):
        state.players[player].hand.remove(self)
        state.battlefield.append(Permanent(card=self, controller=player))

    def activated_abilities(self, state: "GameState", player: int, source_index: int) -> Sequence[CardAbility]:
        permanent = state.battlefield[source_index]
        if permanent.controller != player:
            return []

        abilities: List[CardAbility] = []
        for color in COLORS:
            mana_color = color

            def _sac_for_mana(st: "GameState", pl: int, idx: int, mana_color=mana_color) -> None:
                if idx >= len(st.battlefield):
                    return
                perm = st.battlefield[idx]
                if perm.controller != pl:
                    return
                st.battlefield.pop(idx)
                st.players[pl].graveyard.append(perm.card)
                st.players[pl].mana_pool[mana_color] += 3

            label = f"Sacrifice {self.name} for {mana_color*3}"
            abilities.append(CardAbility(description=label, source_index=source_index, executor=_sac_for_mana))
        return abilities


class LotusPetal(Card):
    def __init__(self):
        super().__init__(name="Lotus Petal", types=("Artifact",), cost_str="0")

    def can_play(self, state, player):
        return True

    def play(self, state, player):
        state.players[player].hand.remove(self)
        state.battlefield.append(Permanent(card=self, controller=player))

    def activated_abilities(self, state: "GameState", player: int, source_index: int) -> Sequence[CardAbility]:
        permanent = state.battlefield[source_index]
        if permanent.controller != player:
            return []

        abilities: List[CardAbility] = []
        for symbol in ALL_MANA_SYMBOLS:
            mana_symbol = symbol

            def _sac_for_mana(st: "GameState", pl: int, idx: int, mana_symbol=mana_symbol) -> None:
                if idx >= len(st.battlefield):
                    return
                perm = st.battlefield[idx]
                if perm.controller != pl:
                    return
                st.battlefield.pop(idx)
                st.players[pl].graveyard.append(perm.card)
                st.players[pl].mana_pool[mana_symbol] += 1

            label = f"Sacrifice {self.name} for {mana_symbol}"
            abilities.append(CardAbility(description=label, source_index=source_index, executor=_sac_for_mana))
        return abilities


class SimpleCreature(Card):
    def __init__(self, name: str, cost: str, power: int, toughness: int, haste: bool = False):
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


CardFactory = Callable[[], Card]
CARD_REGISTRY: Dict[str, CardFactory] = {}


def _canonical(name: str) -> str:
    return name.strip().lower()


def register_card(name: str, factory: CardFactory, aliases: Optional[Iterable[str]] = None) -> None:
    """Register a callable that produces a fresh card instance for ``name``.

    The helper accepts optional ``aliases`` so future decklists can use alternate
    spellings without additional boilerplate.  Factories are expected to return a
    new :class:`Card` instance on each invocation to avoid cross-game state
    leakage.
    """

    keys = {_canonical(name)}
    if aliases:
        keys.update(_canonical(alias) for alias in aliases)
    for key in keys:
        if key in CARD_REGISTRY:
            raise ValueError(f"Card '{name}' (alias '{key}') already registered")
    for key in keys:
        CARD_REGISTRY[key] = factory


def list_registered_cards() -> List[str]:
    """Return a sorted list of canonical card names registered in the library."""

    return sorted(CARD_REGISTRY.keys())


def make_card(name: str) -> Card:
    canonical = _canonical(name)
    try:
        factory = CARD_REGISTRY[canonical]
    except KeyError:
        # Fall back to a simple vanilla creature so casual experiments keep working
        return SimpleCreature(name.title(), cost="2", power=2, toughness=2)
    return factory()


def register_default_cards() -> None:
    register_card("Plains", lambda: BasicLand("Plains", "W"))
    register_card("Island", lambda: BasicLand("Island", "U"))
    register_card("Swamp", lambda: BasicLand("Swamp", "B"))
    register_card("Mountain", lambda: BasicLand("Mountain", "R"))
    register_card("Forest", lambda: BasicLand("Forest", "G"))
    register_card("Wastes", lambda: BasicLand("Wastes", None))
    register_card("Black Lotus", BlackLotus)
    register_card("Lotus Petal", LotusPetal)
    register_card("Grizzly Bears", lambda: SimpleCreature("Grizzly Bears", cost="1G", power=2, toughness=2))
    register_card("Elite Vanguard", lambda: SimpleCreature("Elite Vanguard", cost="W", power=2, toughness=1))
    register_card("Savannah Lions", lambda: SimpleCreature("Savannah Lions", cost="W", power=2, toughness=1))
    register_card("Lightning Bolt", LightningBolt)
    register_card(
        "Vanilla 2/2",
        lambda: SimpleCreature("Vanilla 2/2", cost="2", power=2, toughness=2),
        aliases=["Grizzly Bear"],
    )


register_default_cards()

__all__ = [
    "ALL_MANA_SYMBOLS",
    "BasicLand",
    "BlackLotus",
    "CARD_REGISTRY",
    "COLORS",
    "Card",
    "CardAbility",
    "LotusPetal",
    "LightningBolt",
    "Permanent",
    "SimpleCreature",
    "can_pay",
    "empty_pool",
    "list_registered_cards",
    "make_card",
    "register_card",
    "parse_mana_cost",
    "pay",
]
