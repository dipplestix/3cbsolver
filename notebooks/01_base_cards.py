import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # 01: Base Cards Module

    **File:** `simulator/cards/base.py`

    This module defines the foundational classes for all cards in the 3CB simulator:
    - `CardType` - Enum for card types (LAND, CREATURE, ARTIFACT, ENCHANTMENT)
    - `Action` - Dataclass representing executable game actions
    - `Card` - Abstract base class for all cards

    ## Dependencies
    - None (this is the base layer)

    ## Used By
    - All card implementations (Land, Creature, Artifact, Enchantment)
    - GameState (for type hints)
    - Action generation system
    """)
    return


@app.cell
def _():
    # Setup: Add parent directory to path for imports
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent if "__file__" in dir() else Path.cwd().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return


@app.cell
def _():
    # Import the module we're exploring
    from simulator.cards.base import Card, Action, CardType
    return Action, Card, CardType


@app.cell
def _(mo):
    mo.md("""
    ---
    ## CardType Enum

    Simple enumeration of the four card types in Magic: The Gathering.
    Used for type checking and categorization.
    """)
    return


@app.cell
def _(CardType):
    # Explore CardType enum
    print("CardType values:")
    for ct in CardType:
        print(f"  {ct.name} = {ct.value}")
    return


@app.cell
def _(CardType):
    # CardType usage examples
    land_type = CardType.LAND
    creature_type = CardType.CREATURE

    print(f"Is LAND == CREATURE? {land_type == creature_type}")
    print(f"CardType from name: {CardType['ARTIFACT']}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Action Dataclass

    Actions are the atomic operations in the game. Each action has:
    - `description`: Human-readable string (e.g., "Cast Student of Warfare")
    - `execute`: A function that takes GameState and returns new GameState

    Actions are **immutable** - executing an action creates a NEW state.
    """)
    return


@app.cell
def _(Action):
    # Create a simple example action
    def dummy_execute(state):
        """Example action that just returns the state unchanged."""
        return state

    example_action = Action(
        description="Do Nothing",
        execute=dummy_execute
    )

    print(f"Action: {example_action}")
    print(f"Description: {example_action.description}")
    print(f"Execute function: {example_action.execute}")
    return


@app.cell
def _(Action):
    # Demonstrating action composition
    def make_life_change_action(player: int, amount: int) -> Action:
        """Factory function to create a life-changing action."""
        def execute(state):
            # In real code, this would modify state.life[player]
            new_state = state  # Would be state.copy() in real code
            return new_state

        sign = "+" if amount > 0 else ""
        return Action(
            description=f"Player {player}: {sign}{amount} life",
            execute=execute
        )

    gain_life = make_life_change_action(0, 3)
    lose_life = make_life_change_action(1, -5)

    print(f"Action 1: {gain_life}")
    print(f"Action 2: {lose_life}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Card Abstract Base Class

    The `Card` class is the abstract base for all cards. Key features:

    ### Core Attributes
    - `name`: Card name (string)
    - `owner`: Player index (0 or 1)
    - `tapped`: Whether the card is tapped

    ### Action Methods (override in subclasses)
    - `get_play_actions()`: Actions when card is in hand
    - `get_battlefield_actions()`: Activated abilities on battlefield
    - `get_attack_actions()`: Attack options in combat
    - `get_block_actions()`: Block options in combat

    ### Lifecycle Hooks
    - `on_upkeep()`: Called at start of owner's upkeep
    - `on_end_turn()`: Called at end of turn

    ### Mana Methods
    - `get_mana_output()`: How much mana produced
    - `tap_for_mana()`: Tap and produce mana (with side effects)
    - `should_sacrifice_after_tap()`: For depletion lands

    ### Utility Methods
    - `is_creature()`: Returns True if currently a creature
    - `get_signature_state()`: Hashable state for memoization
    - `copy()`: Abstract - must be implemented by subclasses
    """)
    return


@app.cell
def _(Card):
    # Card is abstract - we can't instantiate it directly
    # Let's see what methods it defines

    print("Card class methods:")
    for name in dir(Card):
        if not name.startswith('_'):
            attr = getattr(Card, name)
            if callable(attr):
                print(f"  {name}()")
    return


@app.cell
def _(Card):
    # Create a minimal concrete implementation for testing
    class TestCard(Card):
        """Minimal Card implementation for testing."""

        def __init__(self, name: str, owner: int):
            super().__init__(name, owner)
            self.custom_data = "test"

        def copy(self):
            new_card = TestCard(self.name, self.owner)
            new_card.tapped = self.tapped
            new_card.custom_data = self.custom_data
            return new_card

    # Create instances
    card1 = TestCard("Test Card", owner=0)
    card2 = TestCard("Another Card", owner=1)

    print(f"Card 1: {card1}")
    print(f"Card 2: {card2}")
    print(f"Card 1 owner: {card1.owner}")
    print(f"Card 1 tapped: {card1.tapped}")
    return (card1,)


@app.cell
def _(card1):
    # Test tapping behavior
    print(f"Before tap: {card1}")
    print(f"  tapped = {card1.tapped}")

    card1.tapped = True
    print(f"After tap: {card1}")
    print(f"  tapped = {card1.tapped}")

    # Reset for other cells
    card1.tapped = False
    return


@app.cell
def _(card1):
    # Test copy semantics
    card1_copy = card1.copy()

    print(f"Original: {card1}, id={id(card1)}")
    print(f"Copy:     {card1_copy}, id={id(card1_copy)}")
    print(f"Same object? {card1 is card1_copy}")
    print(f"Same name? {card1.name == card1_copy.name}")

    # Modify copy - original should be unchanged
    card1_copy.tapped = True
    card1_copy.custom_data = "modified"

    print(f"\nAfter modifying copy:")
    print(f"Original tapped: {card1.tapped}")
    print(f"Copy tapped: {card1_copy.tapped}")
    print(f"Original custom_data: {card1.custom_data}")
    print(f"Copy custom_data: {card1_copy.custom_data}")
    return


@app.cell
def _(card1):
    # Test signature state for memoization
    sig1 = card1.get_signature_state()
    print(f"Signature (untapped): {sig1}")

    card1.tapped = True
    sig2 = card1.get_signature_state()
    print(f"Signature (tapped): {sig2}")

    print(f"\nSignatures equal? {sig1 == sig2}")
    print(f"Signature is hashable? {hash(sig1) is not None}")

    # Reset
    card1.tapped = False
    return


@app.cell
def _(card1):
    # Test default method implementations
    print("Default action methods return empty lists:")
    print(f"  get_play_actions(): {card1.get_play_actions(None)}")
    print(f"  get_battlefield_actions(): {card1.get_battlefield_actions(None)}")
    print(f"  get_attack_actions(): {card1.get_attack_actions(None)}")
    print(f"  get_block_actions(): {card1.get_block_actions(None, [])}")

    print("\nDefault utility methods:")
    print(f"  is_creature(): {card1.is_creature()}")
    print(f"  get_mana_output(): {card1.get_mana_output()}")
    print(f"  should_sacrifice_after_tap(): {card1.should_sacrifice_after_tap()}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Design Patterns

    ### 1. Immutable State Transitions
    Actions don't modify state in-place. They return NEW states:
    ```python
    def execute(state: GameState) -> GameState:
        new_state = state.copy()
        # modify new_state
        return new_state
    ```

    ### 2. Polymorphic Action Generation
    Each card type overrides action methods to provide appropriate options:
    - Lands: `get_play_actions()` for land drops
    - Creatures: `get_attack_actions()`, `get_block_actions()`
    - Artifacts: `get_battlefield_actions()` for tap abilities

    ### 3. Signature-Based Memoization
    `get_signature_state()` returns a hashable tuple that uniquely identifies
    the card's current state. This enables transposition table caching in the solver.

    ### 4. Hook Methods for Lifecycle
    Cards can override `on_upkeep()` and `on_end_turn()` for triggers:
    - Thallid: Add spore counters on upkeep
    - Student of Warfare: Auto-level on upkeep
    - Sleep-Cursed Faerie: Remove stun counters

    ---
    ## Summary

    The base module establishes the contract that all cards must follow:
    1. Cards have a name, owner, and tapped state
    2. Cards can generate actions for different game phases
    3. Cards can be copied (for state branching)
    4. Cards provide a signature for memoization
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
