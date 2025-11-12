from 3cb_simulator import build_deck, play_match, round_robin

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
table = round_robin(decks, search_depth=8, max_turns=20)
print(table)

