"""Card definitions used by the duel simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Card:
    """Represents the minimal data needed for combat in our toy model."""

    name: str
    power: int
    toughness: int


BETA_CARDS: Dict[str, Card] = {
    "Shivan Dragon": Card(name="Shivan Dragon", power=5, toughness=5),
    "Savannah Lions": Card(name="Savannah Lions", power=2, toughness=1),
}


def get_card(name: str) -> Card:
    """Return the card matching *name* from the Beta set.

    Raises:
        KeyError: if *name* is not registered.
    """

    try:
        return BETA_CARDS[name]
    except KeyError as exc:  # pragma: no cover - simple passthrough
        raise KeyError(f"Unknown card: {name}") from exc


__all__ = ["Card", "BETA_CARDS", "get_card"]
