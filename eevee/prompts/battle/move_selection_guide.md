# Pokemon Move Selection Navigation Guide

## Battle Menu Navigation Patterns

### Basic Menu Flow:
1. **Battle Start** → Battle menu appears ("FIGHT", "BAG", "POKEMON", "RUN")
2. **Select FIGHT** → Press ["a"] to access move selection
3. **Move Selection** → 4 moves displayed in grid pattern
4. **Navigate & Select** → Use arrows + A to choose move

### Move Grid Layouts:

**Standard 2x2 Grid:**
```
┌─────────────┬─────────────┐
│ Move 1      │ Move 3      │
│ (A button)  │ (→ + A)     │
├─────────────┼─────────────┤
│ Move 2      │ Move 4      │
│ (↓ + A)     │ (↓ + → + A) │
└─────────────┴─────────────┘
```

**Vertical List Layout:**
```
┌─────────────┐
│ Move 1 (A)  │
├─────────────┤
│ Move 2 (↓A) │
├─────────────┤
│ Move 3 (↓↓A)│
├─────────────┤
│ Move 4 (↓↓↓A)│
└─────────────┘
```

### Button Sequences by Position:

**Position 1 (Top-Left/First):**
- Buttons: `["a"]`
- Usually default selection

**Position 2 (Second):**
- If vertical: `["down", "a"]`
- If 2x2 grid: `["down", "a"]`

**Position 3 (Third):**
- If vertical: `["down", "down", "a"]`
- If 2x2 grid: `["right", "a"]`

**Position 4 (Fourth):**
- If vertical: `["down", "down", "down", "a"]`
- If 2x2 grid: `["down", "right", "a"]`

### Common Move Examples:

**Example 1: Want Thundershock in position 2**
```
Visible moves: "GROWL", "THUNDERSHOCK", "TAIL WHIP", "-"
Action: ["down", "a"]
```

**Example 2: Want Tackle in position 1**
```
Visible moves: "TACKLE", "GROWL", "THUNDERSHOCK", "TAIL WHIP"
Action: ["a"]
```

**Example 3: Want move in position 3 (2x2 grid)**
```
Visible moves: "TACKLE", "GROWL", "THUNDERSHOCK", "TAIL WHIP"
Want: THUNDERSHOCK (position 3)
Action: ["right", "a"]
```

### Troubleshooting Navigation:

**If move selection isn't working:**
1. Ensure you're in move selection screen (not battle menu)
2. Double-check move position in the grid
3. Use single direction button + A (not multiple directions)
4. Wait for animation/text to complete before pressing buttons

**Recovery strategies:**
- Press B to go back to battle menu if needed
- Use A to select FIGHT again
- Re-navigate to desired move