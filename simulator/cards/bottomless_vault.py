"""Bottomless Vault - Storage land that accumulates black mana."""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class BottomlessVault(Land):
    """
    Bottomless Vault
    Land

    Bottomless Vault enters the battlefield tapped.
    You may choose not to untap Bottomless Vault during your untap step.
    At the beginning of your upkeep, if Bottomless Vault is tapped,
    put a storage counter on it.
    T, Remove any number of storage counters from Bottomless Vault:
    Add B for each storage counter removed this way.

    Flow:
    1. Enters tapped, stay_tapped=True
    2. Each upkeep while tapped: +1 storage counter
    3. Main phase choice: "Prepare to release" sets stay_tapped=False
    4. Next untap step: untaps (if stay_tapped=False)
    5. Main phase when untapped: "Tap for XB" converts counters to mana
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Bottomless Vault",
            owner=owner,
            mana_produced='B'
        )
        self.storage_counters = 0
        self.stay_tapped = True  # Whether to skip untapping

    def get_mana_output(self) -> int:
        """Storage lands produce mana equal to storage counters."""
        return self.storage_counters

    def tap_for_mana(self) -> int:
        """Tap and release all storage counters. Returns mana produced."""
        if self.tapped:
            return 0
        mana = self.storage_counters
        self.storage_counters = 0
        self.tapped = True
        return mana

    def get_signature_state(self) -> tuple:
        """Return vault-specific state including storage counters and stay_tapped flag."""
        return (
            self.name,
            self.tapped,
            self.storage_counters,
            self.stay_tapped,
        )

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []
        if state.land_played_this_turn:
            return []

        def play(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    vault = ns.hands[self.owner].pop(i)
                    vault.tapped = True  # Enters tapped
                    vault.stay_tapped = True  # Default to accumulating
                    ns.battlefield[self.owner].append(vault)
                    break
            ns.land_played_this_turn = True
            return ns

        return [Action(f"Play {self.name}", play)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        actions = []

        if self.tapped:
            # If tapped and set to stay tapped, can choose to release next turn
            if self.stay_tapped and self.storage_counters > 0:
                def prepare_release(s: 'GameState') -> 'GameState':
                    ns = s.copy()
                    for card in ns.battlefield[self.owner]:
                        if card.name == self.name and isinstance(card, BottomlessVault):
                            card.stay_tapped = False  # Will untap next turn
                            break
                    return ns
                actions.append(Action(
                    f"Prepare {self.name} to release ({self.storage_counters}B next turn)",
                    prepare_release
                ))
        # Note: No standalone "tap for mana" action - mana is produced via pay_mana()
        # when casting something. Floating mana that isn't used is pointless.

        return actions

    def on_upkeep(self, state: 'GameState') -> 'GameState':
        """At beginning of upkeep, if tapped, add a storage counter."""
        if self.tapped:
            ns = state.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, BottomlessVault):
                    card.storage_counters += 1
                    break
            return ns
        return state

    def copy(self) -> 'BottomlessVault':
        new_vault = BottomlessVault(self.owner)
        new_vault.tapped = self.tapped
        new_vault.storage_counters = self.storage_counters
        new_vault.stay_tapped = self.stay_tapped
        return new_vault


def create_bottomless_vault(owner: int) -> BottomlessVault:
    """Factory function for Bottomless Vault."""
    return BottomlessVault(owner)
