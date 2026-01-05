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
    # 02: GameState Module

    **File:** `simulator/game_state.py`

    The `GameState` dataclass is the central data structure representing the complete
    state of a game at any point in time. It's designed for:

    1. **Immutability** - All state transitions create new states via `copy()`
    2. **Memoization** - `signature()` and `board_signature()` enable caching
    3. **Clarity** - Separate zones for hands, battlefield, artifacts, enchantments, graveyard

    ## Key Design Decisions
    - Turn number NOT included in signature (position matters, not history)
    - Cards provide their own signature state (extensible)
    - Blocking assignments tracked as dict for combat phases
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
    from simulator.game_state import GameState
    from simulator.cards.base import Card
    return Card, GameState


@app.cell
def _(mo):
    mo.md("""
    ---
    ## GameState Fields

    ### Zone Fields (List[List[Card]])
    Each zone is indexed by player: `zone[0]` for P1, `zone[1]` for P2

    | Zone | Description |
    |------|-------------|
    | `life` | Life totals [P1, P2] (default: [20, 20]) |
    | `hands` | Cards in hand |
    | `library` | Cards in deck (draw from index 0) |
    | `battlefield` | Creatures, lands, creature-lands |
    | `artifacts` | Non-creature artifacts (Moxen, etc.) |
    | `enchantments` | Global and aura enchantments |
    | `graveyard` | Dead/discarded cards |
    | `stack` | Spells waiting to resolve (List[Card]) |

    ### Turn/Phase Tracking
    | Field | Description |
    |-------|-------------|
    | `active_player` | Whose turn (0 or 1) |
    | `phase` | Current phase string |
    | `turn` | Turn counter (increments each player's turn) |
    | `land_played_this_turn` | One land per turn tracking |

    ### Combat
    | Field | Description |
    |-------|-------------|
    | `blocking_assignments` | Dict mapping attacker_idx → blocker_idx |

    ### Game End
    | Field | Description |
    |-------|-------------|
    | `game_over` | True when game has ended |
    | `winner` | 0, 1, or None (draw) |

    ### Stalemate Detection
    | Field | Description |
    |-------|-------------|
    | `stale_turns` | Counter for unchanged board states |
    | `prev_main_sig` | Previous main phase signature |
    """)
    return


@app.cell
def _(GameState):
    # Create a default game state
    state = GameState()

    print("Default GameState:")
    print(f"  life: {state.life}")
    print(f"  hands: {state.hands}")
    print(f"  battlefield: {state.battlefield}")
    print(f"  active_player: {state.active_player}")
    print(f"  phase: {state.phase}")
    print(f"  turn: {state.turn}")
    print(f"  game_over: {state.game_over}")
    print(f"  winner: {state.winner}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Phase State Machine

    The game progresses through phases in this order:

    ```
    untap → upkeep → draw* → main1 → combat_attack → combat_block → combat_damage → end_turn
                       ↑        ↓                                                        ↓
                (only if    [cast spell]                                                 ↓
                 library)       ↓                                                        ↓
                            response** ←→ (counter/pass)                                 ↓
                                                        (next player) ← ← ← ← ← ← ← ← ←
    ```

    *Draw phase only triggers if library has cards. Player going first skips turn 1 draw.
    **Response phase triggers when a spell is cast. Opponent can counter with instants.

    Phase transitions are handled by:
    - `phases/untap.py` - Untap permanents
    - `phases/upkeep.py` - Triggers, auto-level, transition to draw or main1
    - `phases/draw.py` - Draw card from library (if applicable)
    - `actions.py` - Main phase → combat, response phase handling
    - `combat.py` - Combat damage resolution
    - `phases/end_turn.py` - Cleanup, player switch
    """)
    return


@app.cell
def _():
    # Valid phases
    PHASES = [
        "untap",
        "upkeep",
        "draw",      # Only if library has cards
        "main1",
        "response",  # When spell cast, opponent can respond
        "combat_attack",
        "combat_block",
        "combat_damage",
        "end_turn"
    ]

    print("Valid phases:")
    for i, phase in enumerate(PHASES):
        print(f"  {i+1}. {phase}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Deep Copy Semantics

    `GameState.copy()` creates a complete deep copy:
    - All lists are copied
    - All cards are copied via `card.copy()`
    - Primitive values are copied by value

    This is essential for minimax search - each branch gets its own state.
    """)
    return


@app.cell
def _(Card, GameState):
    # Create a test card for demonstrations
    class SimpleCard(Card):
        def __init__(self, name, owner):
            super().__init__(name, owner)
        def copy(self):
            c = SimpleCard(self.name, self.owner)
            c.tapped = self.tapped
            return c

    # Create state with some cards
    test_state = GameState(
        life=[20, 18],
        hands=[[SimpleCard("Card A", 0)], [SimpleCard("Card B", 1)]],
        battlefield=[[SimpleCard("Land", 0)], []],
        active_player=0,
        phase="main1",
        turn=3
    )

    print("Original state:")
    print(f"  life: {test_state.life}")
    print(f"  hands[0]: {[c.name for c in test_state.hands[0]]}")
    print(f"  battlefield[0]: {[c.name for c in test_state.battlefield[0]]}")
    return SimpleCard, test_state


@app.cell
def _(test_state):
    # Copy and modify
    copied_state = test_state.copy()

    # Modify copy
    copied_state.life[0] = 15
    copied_state.hands[0][0].tapped = True
    copied_state.phase = "combat_attack"

    print("After modifying COPY:")
    print(f"\nOriginal state:")
    print(f"  life: {test_state.life}")
    print(f"  hands[0][0].tapped: {test_state.hands[0][0].tapped}")
    print(f"  phase: {test_state.phase}")

    print(f"\nCopied state:")
    print(f"  life: {copied_state.life}")
    print(f"  hands[0][0].tapped: {copied_state.hands[0][0].tapped}")
    print(f"  phase: {copied_state.phase}")

    print(f"\nOriginal unchanged? {test_state.life[0] == 20}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Mana System

    GameState provides methods for mana management:

    ### Query Methods
    - `get_available_mana(player)` - Total untapped mana count
    - `get_available_mana_by_color(player)` - Dict of color → count

    ### Payment Methods
    - `pay_mana(player, color, amount)` - Pay specific color, returns new state
    - `pay_generic_mana(player, amount)` - Pay any color (colorless first)

    ### Key Behaviors
    - Creature lands with summoning sickness can't tap for mana
    - Depletion lands sacrifice after tapping
    - Colorless mana ('C') is prioritized for generic costs
    """)
    return


@app.cell
def _(GameState, SimpleCard):
    # Create a simple land-like card for mana testing
    class SimpleLand(SimpleCard):
        def __init__(self, name, owner, color):
            super().__init__(name, owner)
            self.mana_produced = color

        def get_mana_output(self):
            return 1

        def tap_for_mana(self):
            if self.tapped:
                return 0
            self.tapped = True
            return 1

        def should_sacrifice_after_tap(self):
            return False

        def copy(self):
            c = SimpleLand(self.name, self.owner, self.mana_produced)
            c.tapped = self.tapped
            return c

    # Create state with lands
    mana_state = GameState(
        battlefield=[
            [SimpleLand("Plains", 0, "W"), SimpleLand("Forest", 0, "G")],
            [SimpleLand("Island", 1, "U")]
        ]
    )

    print("Mana state battlefield:")
    print(f"  P0: {[c.name for c in mana_state.battlefield[0]]}")
    print(f"  P1: {[c.name for c in mana_state.battlefield[1]]}")
    return (mana_state,)


@app.cell
def _(mana_state):
    # Test mana queries
    p0_mana = mana_state.get_available_mana(0)
    p0_mana_by_color = mana_state.get_available_mana_by_color(0)

    print(f"Player 0 available mana: {p0_mana}")
    print(f"Player 0 mana by color: {p0_mana_by_color}")

    p1_mana = mana_state.get_available_mana(1)
    p1_mana_by_color = mana_state.get_available_mana_by_color(1)

    print(f"\nPlayer 1 available mana: {p1_mana}")
    print(f"Player 1 mana by color: {p1_mana_by_color}")
    return


@app.cell
def _(mana_state):
    # Test paying mana
    print("Before paying mana:")
    print(f"  Plains tapped: {mana_state.battlefield[0][0].tapped}")
    print(f"  Available W: {mana_state.get_available_mana_by_color(0).get('W', 0)}")

    # Pay 1 white mana
    after_pay = mana_state.pay_mana(player=0, color='W', amount=1)

    print("\nAfter paying 1W:")
    print(f"  Original Plains tapped: {mana_state.battlefield[0][0].tapped}")
    print(f"  New state Plains tapped: {after_pay.battlefield[0][0].tapped}")
    print(f"  Available W: {after_pay.get_available_mana_by_color(0).get('W', 0)}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Signature System

    Two signature methods enable memoization in the solver:

    ### `signature()` - Full State Signature
    Includes everything needed to identify a unique game position:
    - Life totals
    - Active player
    - Land played this turn
    - All card zones (hands, battlefield, artifacts, enchantments)
    - Blocking assignments

    **NOT included:** Turn number (only position matters, not how we got there)

    ### `board_signature()` - Board-Only Signature
    Same as `signature()` but excludes life totals. Used for dominance pruning:
    - If two states have same board but different life totals
    - The state with higher life for both players dominates
    """)
    return


@app.cell
def _(test_state):
    # Test signature
    sig = test_state.signature()

    print("Signature components:")
    print(f"  Type: {type(sig)}")
    print(f"  Length: {len(sig)}")
    print(f"  Hashable: {hash(sig) is not None}")
    print(f"\nSignature value:\n{sig}")
    return


@app.cell
def _(test_state):
    # Test board_signature (excludes life)
    board_sig = test_state.board_signature()

    print("Board signature (no life):")
    print(f"  Length: {len(board_sig)}")
    print(f"\nBoard signature value:\n{board_sig}")
    return


@app.cell
def _(test_state):
    # Demonstrate signature difference with life change
    modified = test_state.copy()
    modified.life[0] = 10

    orig_sig = test_state.signature()
    mod_sig = modified.signature()
    orig_board = test_state.board_signature()
    mod_board = modified.board_signature()

    print(f"Life changed: 20 → 10")
    print(f"\nFull signatures equal? {orig_sig == mod_sig}")
    print(f"Board signatures equal? {orig_board == mod_board}")
    print("\n→ This enables dominance pruning!")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Combat Helpers

    ### `get_attackers()`
    Returns all creatures marked as attacking for the active player.

    ### `get_creatures(player)`
    Returns all cards that are currently creatures for a player.
    Uses the `is_creature()` method which handles creature lands.
    """)
    return


@app.cell
def _(Card, GameState):
    # Create creature-like cards for testing
    class TestCreature(Card):
        def __init__(self, name, owner):
            super().__init__(name, owner)
            self.attacking = False
            self.power = 2
            self.toughness = 2

        def is_creature(self):
            return True

        def copy(self):
            c = TestCreature(self.name, self.owner)
            c.tapped = self.tapped
            c.attacking = self.attacking
            return c

    # Create combat state
    combat_state = GameState(
        battlefield=[
            [TestCreature("Attacker 1", 0), TestCreature("Attacker 2", 0)],
            [TestCreature("Blocker", 1)]
        ],
        active_player=0,
        phase="combat_attack"
    )

    # Mark one as attacking
    combat_state.battlefield[0][0].attacking = True

    print("Combat state:")
    print(f"  P0 creatures: {[c.name for c in combat_state.get_creatures(0)]}")
    print(f"  P1 creatures: {[c.name for c in combat_state.get_creatures(1)]}")
    print(f"  Attackers: {[c.name for c in combat_state.get_attackers()]}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Stalemate Detection

    Added to handle symmetric matchups (e.g., Student vs Student):

    - `stale_turns`: Counter incremented when board unchanged
    - `prev_main_sig`: Signature from previous main phase

    If `stale_turns >= 10` (5 full rounds), game ends in draw.

    This is checked in `phases/upkeep.py`.
    """)
    return


@app.cell
def _(GameState):
    # Stalemate tracking fields
    stale_state = GameState()

    print("Stalemate tracking:")
    print(f"  stale_turns: {stale_state.stale_turns}")
    print(f"  prev_main_sig: {stale_state.prev_main_sig}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Summary

    `GameState` is the core data structure that:

    1. **Tracks all game zones** - Hands, library, battlefield, artifacts, enchantments, graveyard
    2. **Manages turn/phase flow** - Active player, current phase, turn count
    3. **Handles mana** - Query and payment with summoning sickness, sacrifices
    4. **Enables memoization** - Signature system for transposition tables
    5. **Supports dominance pruning** - Board signatures without life
    6. **Detects stalemates** - Tracks unchanged board states
    7. **Supports card draw** - Library zone with automatic draw phase

    ### Key Properties
    - **Immutable transitions** - `copy()` before modification
    - **Hashable signatures** - Enable caching in solver
    - **Card-driven** - Cards provide their own signature state
    """)
    return


if __name__ == "__main__":
    app.run()
