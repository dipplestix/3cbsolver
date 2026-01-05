import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # 09: Action Generation

        **File:** `simulator/actions.py`

        Generates all legal actions for each phase:
        - **main1**: Play cards, activate abilities, pass to combat
        - **response**: Counter spells or pass to resolve stack
        - **combat_attack**: All attack combinations (2^n)
        - **combat_block**: Block assignments

        ## Key Insight
        The branching factor comes primarily from attack combinations.
        With n creatures, there are 2^n possible attack subsets.
        """
    )
    return


@app.cell
def _():
    # Setup: Add parent directory to path for imports
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent if "__file__" in dir() else Path.cwd().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return Path, project_root, sys


@app.cell
def _():
    from simulator.actions import get_available_actions
    from simulator.game_state import GameState
    from simulator.cards.land import Land
    from simulator.cards.creature import Creature
    return Creature, GameState, Land, get_available_actions


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Main Phase Actions

        During main phase, collect actions from:
        1. **Hand cards** - `card.get_play_actions(state)`
        2. **Battlefield cards** - `card.get_battlefield_actions(state)`
        3. **Always available** - "Pass to Combat"

        ### Auto-Level on Pass
        When passing to combat, auto-level creatures trigger:
        ```python
        def pass_to_combat(s):
            ns = s.copy()
            for card in ns.battlefield[player]:
                if hasattr(card, 'auto_level') and card.auto_level:
                    ns = card.do_auto_level(ns)
            ns.phase = "combat_attack"
            return ns
        ```
        """
    )
    return


@app.cell
def _(Creature, GameState, Land, get_available_actions):
    # Main phase actions example
    test_creature = Creature("Test Creature", 0, 2, 2, {'W': 1})
    test_land = Land("Plains", 0, 'W')

    main_state = GameState(
        hands=[[test_creature, test_land], []],
        battlefield=[[Land("Plains", 0, 'W')], []],  # Already have one land
        phase="main1",
        active_player=0,
        land_played_this_turn=False
    )

    main_actions = get_available_actions(main_state)

    print("Main Phase Actions:")
    for action in main_actions:
        print(f"  - {action.description}")
    return main_actions, main_state, test_creature, test_land


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Attack Phase Actions

        Generate ALL subsets of eligible attackers (2^n combinations).

        ### Eligibility
        - Is a creature
        - Not tapped
        - Not already attacking
        - No summoning sickness (`entered_this_turn=False`)
        - `can_attack()` returns True

        ### Deduplication
        Identical creatures (same signature) are deduplicated to reduce branching.

        ```python
        sig = (card.name, power, toughness, plus_counters, level, eot_boosts...)
        if sig in seen_sigs:
            continue  # Skip duplicate
        ```
        """
    )
    return


@app.cell
def _(Creature, GameState, Land, get_available_actions):
    # Attack phase with multiple creatures
    creature1 = Creature("Soldier A", 0, 2, 2, {'W': 1})
    creature1.entered_this_turn = False  # Can attack
    creature2 = Creature("Soldier B", 0, 2, 2, {'W': 1})
    creature2.entered_this_turn = False  # Can attack
    creature3 = Creature("New Guy", 0, 3, 3, {'G': 1})
    creature3.entered_this_turn = True  # Summoning sickness

    attack_state = GameState(
        battlefield=[
            [Land("Plains", 0, 'W'), creature1, creature2, creature3],
            []
        ],
        phase="combat_attack",
        active_player=0
    )

    attack_actions = get_available_actions(attack_state)

    print("Attack Phase Actions:")
    print(f"  Eligible: Soldier A, Soldier B (New Guy has summoning sickness)")
    print(f"  But Soldier A & B are identical → deduplicated to 1")
    print(f"\nGenerated actions ({len(attack_actions)}):")
    for action in attack_actions:
        print(f"  - {action.description}")
    return (
        attack_actions,
        attack_state,
        creature1,
        creature2,
        creature3,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Attack Combination Math

        Without deduplication: 2^n actions for n creatures
        - 1 creature: 2 actions (attack, no attack)
        - 2 creatures: 4 actions
        - 3 creatures: 8 actions
        - 4 creatures: 16 actions

        With deduplication: 2^unique_types
        - 3 identical soldiers: 2 actions (any subset of "soldier")
        - 2 soldiers + 1 different: 4 actions

        Deduplication is critical for performance!
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Block Phase Actions

        For each unblocked attacker, generate block options:
        1. Collect eligible blockers (untapped, can block this attacker)
        2. Check flying/reach rules
        3. Check "can't be blocked by" restrictions
        4. Generate one action per valid blocker assignment
        5. Always include "No Block" option

        ### Deduplication
        Similar to attacks, identical blocker/attacker pairs are deduplicated.
        """
    )
    return


@app.cell
def _(Creature, GameState, get_available_actions):
    # Block phase example
    attacker_creature = Creature("Attacker", 0, 3, 3, {'R': 1})
    attacker_creature.attacking = True

    blocker1 = Creature("Blocker A", 1, 2, 2, {'W': 1})
    blocker2 = Creature("Blocker B", 1, 2, 4, {'W': 1})

    block_state = GameState(
        battlefield=[
            [attacker_creature],
            [blocker1, blocker2]
        ],
        blocking_assignments={},
        phase="combat_block",
        active_player=0  # P0 is attacking
    )

    block_actions = get_available_actions(block_state)

    print("Block Phase Actions:")
    print(f"  Attacker: 3/3")
    print(f"  Blockers: 2/2, 2/4")
    print(f"\nGenerated actions ({len(block_actions)}):")
    for action in block_actions:
        print(f"  - {action.description}")
    return (
        attacker_creature,
        block_actions,
        block_state,
        blocker1,
        blocker2,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Response Phase Actions

        When a spell is cast, it goes on the `stack` and phase becomes `"response"`.
        The **opponent of the top spell's owner** can then respond.

        ### Who Responds?
        ```python
        top_spell_owner = state.stack[-1].owner
        responder = 1 - top_spell_owner
        ```

        This enables **counter-wars**: if P1 casts a creature and P2 counters it,
        P1 can counter the counter (since P1 is the opponent of the counter's owner).

        ### Available Actions
        1. **Cast instants** - e.g., Mental Misstep, Daze
        2. **Pass** - Resolve the top spell on the stack

        ### Counter-War Example
        ```
        Stack: [Creature(P1), Mental Misstep(P2)]
        Top spell owner: P2
        Responder: P1

        P1 can now cast Daze targeting Mental Misstep!
        Stack becomes: [Creature(P1), Mental Misstep(P2), Daze(P1)]
        Now P2 responds to Daze...
        ```

        ### Resolution Flow
        1. Spell cast → goes on stack, phase = "response"
        2. Opponent of top spell's owner: cast instant or pass
        3. If pass → resolve top of stack, remove from stack
        4. Repeat until stack empty → return to main1
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Flying and Reach

        ```python
        def can_block(self, attacker):
            if attacker.has_flying:
                if not self.has_flying and 'reach' not in self.keywords:
                    return False  # Can't block flyer
            return True
        ```

        Ground creatures can't block flyers unless they have reach.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Action Structure

        Each action is an `Action` dataclass:
        ```python
        @dataclass
        class Action:
            description: str
            execute: Callable[[GameState], GameState]
        ```

        The `execute` function:
        1. Copies the state
        2. Modifies the copy
        3. Returns the new state

        Actions are **pure functions** - no side effects on input.
        """
    )
    return


@app.cell
def _(main_actions, main_state):
    # Execute an action
    if main_actions:
        first_action = main_actions[0]
        print(f"Executing: {first_action.description}")
        print(f"\nBefore:")
        print(f"  Hands: {[c.name for c in main_state.hands[0]]}")

        new_state = first_action.execute(main_state)
        print(f"\nAfter:")
        print(f"  Hands: {[c.name for c in new_state.hands[0]]}")
        print(f"\nOriginal unchanged:")
        print(f"  Hands: {[c.name for c in main_state.hands[0]]}")
    return first_action, new_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Phase | Actions From | Decision Maker | Branching |
        |-------|--------------|----------------|-----------|
        | main1 | Hand + Battlefield + Pass | Active player | Variable |
        | response | Instants + Pass | Opponent of top spell owner | Low (usually 1-2) |
        | combat_attack | All attack subsets | Active player | 2^n (deduplicated) |
        | combat_block | All block assignments | Defender | #blockers × #attackers |

        ### Key Optimizations
        1. **Deduplication** - Identical creatures share signatures
        2. **Auto-level on pass** - Reduces branching from level choices
        3. **Larger sets first** - Alpha-beta pruning works better
        4. **Spell targeting in signatures** - Prevents cache pollution in counter-wars

        The action generation system is the primary source of branching
        in the game tree.
        """
    )
    return


if __name__ == "__main__":
    app.run()
