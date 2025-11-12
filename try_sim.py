"""Small harness for exercising the 3CB simulator.

This script intentionally lives alongside :mod:`3cb_simulator`, whose filename
starts with a digit.  Python does not allow importing such modules with the
normal ``import`` statement, so we need to load it dynamically instead of using
``from 3cb_simulator import ...`` which raises ``SyntaxError`` when the file is
executed.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys


def _load_simulator_module():
    """Dynamically load the ``3cb_simulator`` module.

    The helper returns the imported module object, ensuring the script keeps a
    stable reference in ``sys.modules`` so repeated imports behave as expected.
    """

    module_name = "threecb_simulator"
    module_path = pathlib.Path(__file__).with_name("3cb_simulator.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load simulator module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


simulator = _load_simulator_module()
build_deck = simulator.build_deck
play_match = simulator.play_match
round_robin = simulator.round_robin

# Define decks by card names (3 cards each)
A = build_deck(["Plains", "Elite Vanguard", "Savannah Lions"])
B = build_deck(["Mountain", "Lightning Bolt", "Grizzly Bears"])

# Compute best-of-two match result
res = play_match(A, B, search_depth=8, max_turns=20)
print(res)
# => {
#   'game1_A_on_play': 0,     #  1 = A wins on play, 0 = draw, -1 = A loses on play
#   'game2_B_on_play': 0,     #  same encoding, second game has B on the play
#   'A_points': 1.0,          #  3CB per-game points summed across the two games
#   'B_points': 1.0
# }

# Round-robin over a small gauntlet
decks = {
    "White Weenie": ["Plains", "Elite Vanguard", "Savannah Lions"],
    "Red BurnBear": ["Mountain", "Lightning Bolt", "Grizzly Bears"],
    "Lotus Lions":  ["Plains", "Black Lotus", "Savannah Lions"],
}
try:
    table = round_robin(decks, search_depth=8, max_turns=20)
except ModuleNotFoundError as exc:
    if exc.name == "pandas":
        print("Round-robin demo skipped: install pandas to view the table output.")
    else:
        raise
else:
    print(table)

