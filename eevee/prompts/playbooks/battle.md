# Pokemon Battle Expert Playbook

**CRITICAL BATTLE NAVIGATION RULES:**

**🎯 MOVE SELECTION PROCESS:**
1. **When you see the battle menu** ("FIGHT", "BAG", "POKEMON", "RUN"):
   - Press **A** to select "FIGHT" (usually first option)

2. **When you see move options** (like "GROWL", "THUNDERSHOCK", "TAIL WHIP"):
   - **DO NOT just press A repeatedly**
   - **READ each move name carefully**
   - **Use DOWN arrow** to navigate to the desired move
   - **Then press A** to select it

3. **Move Selection Priority:**
   - **Offensive moves** (Tackle, Thundershock, Scratch) are preferred for damage
   - **Status moves** (Growl, Tail Whip) can be useful but don't deal damage
   - **Type effective moves** should be prioritized when known

**BATTLE ANALYSIS PROCESS:**

1. **OBSERVE:**
   - What screen elements are visible?
   - Are move names displayed? List them all
   - What is the opponent Pokemon?
   - What is my Pokemon's HP status?

2. **ANALYZE:**
   - Which moves are offensive vs status moves?
   - What types are involved in this battle?
   - What move would be most effective?
   - Do I need to heal or can I continue fighting?

3. **PLAN BUTTON SEQUENCE:**
   - If battle menu visible: ["a"] to select FIGHT
   - If moves visible and want move #1: ["a"]
   - If moves visible and want move #2: ["down", "a"]
   - If moves visible and want move #3: ["right", "a"] (if 2x2 grid)
   - If moves visible and want move #4: ["down", "right", "a"] (if 2x2 grid)

**TYPE EFFECTIVENESS MATRIX:**

**Super Effective (2x damage):**
- **Electric** → Water, Flying
- **Water** → Rock, Ground, Fire
- **Fire** → Grass, Ice, Bug, Steel
- **Grass** → Water, Ground, Rock
- **Ground** → Electric, Fire, Poison, Rock, Steel
- **Rock** → Fire, Ice, Flying, Bug
- **Flying** → Grass, Fighting, Bug
- **Fighting** → Normal, Ice, Rock, Dark, Steel
- **Psychic** → Fighting, Poison
- **Ice** → Grass, Ground, Flying, Dragon
- **Bug** → Grass, Psychic, Dark
- **Poison** → Grass, Fairy
- **Steel** → Ice, Rock, Fairy
- **Dark** → Psychic, Ghost
- **Ghost** → Psychic, Ghost
- **Dragon** → Dragon
- **Fairy** → Fighting, Dragon, Dark

**Not Very Effective (0.5x damage):**
- **Electric** → Grass, Electric, Dragon
- **Water** → Water, Grass, Dragon
- **Fire** → Fire, Water, Rock, Dragon
- **Grass** → Fire, Grass, Poison, Flying, Bug, Dragon, Steel
- **Ground** → Grass, Bug (Flying immune)
- **Fighting** → Flying, Poison, Bug, Psychic, Ghost, Fairy

**No Effect (0x damage):**
- **Electric** → Ground
- **Ground** → Flying
- **Fighting** → Ghost
- **Psychic** → Dark
- **Normal/Fighting** → Ghost

**SMART MOVE SELECTION ALGORITHM:**

1. **Identify Move Types**: 
   - Thundershock = Electric
   - Bubble/Water Gun = Water  
   - Ember/Flamethrower = Fire
   - Vine Whip/Razor Leaf = Grass
   - Tackle/Scratch/Quick Attack = Normal
   - Growl/Tail Whip/Leer = Status (no damage)

2. **Opponent Type Recognition**:
   - Pidgey/Spearow = Normal/Flying
   - Rattata/Raticate = Normal
   - Caterpie/Weedle = Bug
   - Geodude/Onix = Rock/Ground
   - Zubat = Poison/Flying
   - Magikarp = Water
   - Psyduck = Water
   - Machop = Fighting

3. **Priority System**:
   - **First Priority**: Super effective moves (2x damage)
   - **Second Priority**: Neutral offensive moves  
   - **Third Priority**: Not very effective moves (still damage)
   - **Last Resort**: Status moves (no damage)

**BATTLE DECISION TREE:**
1. Can I use a super effective move? → Use it
2. Do I have a strong neutral move? → Use it
3. Is my Pokemon low HP? → Consider switching/healing
4. All moves not very effective? → Use strongest available
5. Only status moves? → Use one that helps (like reducing opponent's attack)

**CRITICAL REMINDERS:**
- **Never just spam A button** in move selection
- **Always read move names** before selecting
- **Use direction buttons** to navigate to desired moves
- **Calculate type effectiveness** before choosing moves
- **Prioritize DAMAGE over status effects** in most battles