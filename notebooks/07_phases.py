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
        # 07: Phase Handlers

        **Files:**
        - `simulator/phases/untap.py`
        - `simulator/phases/upkeep.py`
        - `simulator/phases/draw.py`
        - `simulator/phases/end_turn.py`

        ## Phase Flow
        ```
        untap → upkeep → draw* → main1 → [response**] → combat → end_turn
                                                                      ↓
        (next player) ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
        ```

        *Draw phase only if library has cards. Player 0 skips turn 1 draw.
        **Response phase triggers when spell cast, opponent can counter.

        Phase handlers are **automatic** - no player choices, just state transitions.
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
    from simulator.phases import untap, upkeep, draw, end_turn
    from simulator.game_state import GameState
    from simulator.cards.land import Land
    from simulator.cards.creature import Creature
    return Creature, GameState, Land, draw, end_turn, untap, upkeep


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Untap Phase

        **File:** `simulator/phases/untap.py`

        ### Actions
        1. Untap all permanents (unless stun counters)
        2. Clear `entered_this_turn` (summoning sickness ends)
        3. Reset combat triggers (`targeted_this_turn`, `combat_trigger_used`)
        4. Handle bounce lands (`return_to_hand`)
        5. Transition to upkeep

        ### Stun Counters
        If a card has stun counters, one is removed instead of untapping.
        The card stays tapped.
        """
    )
    return


@app.cell
def _(Creature, GameState, Land, untap):
    # Create a state to test untap
    tapped_land = Land("Plains", 0, 'W')
    tapped_land.tapped = True

    creature_with_ss = Creature("Soldier", 0, 2, 2, {'W': 1})
    creature_with_ss.entered_this_turn = True  # Has summoning sickness

    untap_state = GameState(
        battlefield=[[tapped_land, creature_with_ss], []],
        phase="untap",
        active_player=0
    )

    print("Before untap:")
    print(f"  Plains tapped: {untap_state.battlefield[0][0].tapped}")
    print(f"  Creature summoning sickness: {untap_state.battlefield[0][1].entered_this_turn}")
    print(f"  Phase: {untap_state.phase}")

    after_untap = untap(untap_state)

    print("\nAfter untap:")
    print(f"  Plains tapped: {after_untap.battlefield[0][0].tapped}")
    print(f"  Creature summoning sickness: {after_untap.battlefield[0][1].entered_this_turn}")
    print(f"  Phase: {after_untap.phase}")
    return after_untap, creature_with_ss, tapped_land, untap_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Upkeep Phase

        **File:** `simulator/phases/upkeep.py`

        ### Actions
        1. Call `on_upkeep()` for active player's cards (triggers)
        2. Call `on_opponent_upkeep()` for opponent's enchantments
        3. Check for game over (life <= 0)
        4. **Auto-level** creatures with `auto_level=True`
        5. **Stalemate detection** - Track board signatures
        6. Transition to main1
        """
    )
    return


@app.cell
def _(GameState, Land, upkeep):
    # Test upkeep phase
    upkeep_state = GameState(
        battlefield=[[Land("Plains", 0, 'W')], []],
        phase="upkeep",
        active_player=0,
        stale_turns=0,
        prev_main_sig=None
    )

    print("Before upkeep:")
    print(f"  Phase: {upkeep_state.phase}")
    print(f"  stale_turns: {upkeep_state.stale_turns}")
    print(f"  prev_main_sig: {upkeep_state.prev_main_sig}")

    after_upkeep = upkeep(upkeep_state)

    print("\nAfter upkeep:")
    print(f"  Phase: {after_upkeep.phase}")
    print(f"  stale_turns: {after_upkeep.stale_turns}")
    print(f"  prev_main_sig set: {after_upkeep.prev_main_sig is not None}")
    return after_upkeep, upkeep_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Stalemate Detection in Upkeep

        Each upkeep, the phase handler:
        1. Computes board signature (battlefield, hands, artifacts, enchantments)
        2. Compares to `prev_main_sig`
        3. If same: `stale_turns += 1`
        4. If different: `stale_turns = 0`
        5. If `stale_turns >= 10`: Game ends in draw

        This detects symmetric stalemates like Student vs Student.
        """
    )
    return


@app.cell
def _(GameState, upkeep):
    # Simulate stalemate detection
    stale_state = GameState(
        battlefield=[[], []],
        hands=[[], []],
        phase="upkeep",
        stale_turns=9,  # One away from draw
        prev_main_sig=((), (), (), (), (), (), (), ())  # Empty sig
    )

    after_stale = upkeep(stale_state)

    print("Stalemate detection test (stale_turns=9):")
    print(f"  After upkeep stale_turns: {after_stale.stale_turns}")
    print(f"  Game over: {after_stale.game_over}")
    print(f"  Winner: {after_stale.winner}")
    return after_stale, stale_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Draw Phase

        **File:** `simulator/phases/draw.py`

        ### Conditions
        - Only triggers if library has 1+ cards (checked in upkeep)
        - Player 0 skips draw on turn 1 (going first rule)
        - No deck-out loss for empty library

        ### Actions
        1. Pop top card from `library[active_player]`
        2. Append to `hands[active_player]`
        3. Transition to main1
        """
    )
    return


@app.cell
def _(GameState, Land, draw):
    # Test draw phase
    test_card = Land("Mountain", 0, 'R')
    draw_state = GameState(
        library=[[test_card], []],
        hands=[[], []],
        phase="draw",
        active_player=0,
        turn=2  # Not turn 1, so draw happens
    )

    print("Before draw:")
    print(f"  Library P0: {[c.name for c in draw_state.library[0]]}")
    print(f"  Hand P0: {[c.name for c in draw_state.hands[0]]}")
    print(f"  Turn: {draw_state.turn}")

    after_draw = draw(draw_state)

    print("\nAfter draw:")
    print(f"  Library P0: {[c.name for c in after_draw.library[0]]}")
    print(f"  Hand P0: {[c.name for c in after_draw.hands[0]]}")
    print(f"  Phase: {after_draw.phase}")
    return after_draw, draw_state, test_card


@app.cell
def _(GameState, Land, draw):
    # Test turn 1 skip for player 0
    skip_card = Land("Plains", 0, 'W')
    skip_state = GameState(
        library=[[skip_card], []],
        hands=[[], []],
        phase="draw",
        active_player=0,
        turn=1  # Turn 1 - player 0 skips draw
    )

    print("Turn 1 draw skip test:")
    print(f"  Library before: {[c.name for c in skip_state.library[0]]}")

    after_skip = draw(skip_state)

    print(f"  Library after: {[c.name for c in after_skip.library[0]]}")
    print(f"  Hand after: {[c.name for c in after_skip.hands[0]]}")
    print(f"  → Player 0 skipped turn 1 draw!")
    return after_skip, skip_card, skip_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Response Phase

        **File:** `simulator/actions.py` (handled in `_get_response_actions`)

        ### Trigger
        When a spell is cast, it goes on the `stack` and phase becomes `"response"`.

        ### Actions
        1. Non-active player gets priority
        2. Can cast instants (e.g., Mental Misstep to counter)
        3. Can pass → top of stack resolves
        4. After resolution, check if stack empty → return to main1

        ### Stack Flow
        ```
        main1 → [cast spell] → response → [counter or pass] → resolve → main1
                                   ↓
                            (if instant cast, stays in response)
        ```

        ### Response Actions (from actions.py)
        - Get instant actions from non-active player's hand
        - Always include "Pass (resolve spell)" option
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## End Turn Phase

        **File:** `simulator/phases/end_turn.py`

        ### Actions
        1. Reset `attacking` flag on creatures
        2. Clear damage on ALL creatures
        3. Clear end-of-turn boosts (`eot_power_boost`, `eot_toughness_boost`)
        4. Deactivate creature lands (`_is_creature = False`)
        5. Clear blocking assignments
        6. Switch active player
        7. Reset `land_played_this_turn`
        8. Increment turn counter
        9. Transition to untap
        """
    )
    return


@app.cell
def _(Creature, GameState, end_turn):
    # Test end turn
    attacking_creature = Creature("Attacker", 0, 3, 3, {'R': 1})
    attacking_creature.attacking = True
    attacking_creature.damage = 2  # Took some damage

    damaged_creature = Creature("Defender", 1, 2, 2, {'W': 1})
    damaged_creature.damage = 1

    eot_state = GameState(
        battlefield=[[attacking_creature], [damaged_creature]],
        phase="end_turn",
        active_player=0,
        turn=5,
        land_played_this_turn=True
    )

    print("Before end turn:")
    print(f"  Attacker.attacking: {eot_state.battlefield[0][0].attacking}")
    print(f"  Attacker.damage: {eot_state.battlefield[0][0].damage}")
    print(f"  Defender.damage: {eot_state.battlefield[1][0].damage}")
    print(f"  Active player: {eot_state.active_player}")
    print(f"  Turn: {eot_state.turn}")
    print(f"  Land played: {eot_state.land_played_this_turn}")

    after_eot = end_turn(eot_state)

    print("\nAfter end turn:")
    print(f"  Attacker.attacking: {after_eot.battlefield[0][0].attacking}")
    print(f"  Attacker.damage: {after_eot.battlefield[0][0].damage}")
    print(f"  Defender.damage: {after_eot.battlefield[1][0].damage}")
    print(f"  Active player: {after_eot.active_player}")
    print(f"  Turn: {after_eot.turn}")
    print(f"  Land played: {after_eot.land_played_this_turn}")
    print(f"  Phase: {after_eot.phase}")
    return after_eot, attacking_creature, damaged_creature, eot_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Phase Transitions in Solver

        The solver calls phase handlers directly for automatic phases:

        ```python
        if state.phase == "untap":
            new_state = untap(state)
            return minimax(new_state, ...)

        if state.phase == "upkeep":
            new_state = upkeep(state)
            return minimax(new_state, ...)

        if state.phase == "draw":
            new_state = draw(state)
            return minimax(new_state, ...)

        if state.phase == "end_turn":
            new_state = end_turn(state)
            return minimax(new_state, ...)
        ```

        No action generation needed - these phases have no choices.

        **Exception:** Response phase uses action generation (instants or pass).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Phase | Key Actions | Next Phase |
        |-------|-------------|------------|
        | untap | Untap permanents, clear summoning sickness | upkeep |
        | upkeep | Triggers, auto-level, stalemate check | draw or main1 |
        | draw | Draw card from library (if applicable) | main1 |
        | response | Counter spell or pass to resolve | main1 (after stack empty) |
        | end_turn | Clear damage/combat, switch player | untap |

        ### Important State Changes
        - **untap**: `tapped=False`, `entered_this_turn=False`
        - **upkeep**: `stale_turns++`, auto-level creatures, check library for draw
        - **draw**: Move top of library to hand (P0 skips turn 1)
        - **response**: Stack spells, resolve or counter
        - **end_turn**: `damage=0`, `attacking=False`, `active_player` switches
        """
    )
    return


if __name__ == "__main__":
    app.run()
