# Pokemon Gemma VLM Training Data Format

## JSONL Format Specification

Each line in the training JSONL file represents one training example with 4-frame temporal sequences:

```json
{
  "frames": [
    "/path/to/frame_t0.png",
    "/path/to/frame_t1.png", 
    "/path/to/frame_t2.png",
    "/path/to/frame_t3.png"
  ],
  "context": "Ash navigating Route 1 with Pikachu, health full, 3 Pokeballs remaining",
  "question": "Analyze the 4-frame sequence and determine the optimal next action.",
  "output": "{\"button\": \"right\", \"reasoning\": \"clear_path_east\", \"context\": \"navigation\", \"scene_description\": \"overworld_route_grassy_area\"}"
}
```

## Data Fields

### `frames` (List[str])
- **Required**: Exactly 4 image file paths
- **Format**: Absolute paths to PNG/JPG files
- **Sequence**: Temporal order t0 → t1 → t2 → t3 (each ~250ms apart)
- **Resolution**: Game Boy Advance 240x160 pixels
- **Example**: 4 consecutive frames showing character movement

### `context` (str)
- **Required**: Rich game state context for 32K token utilization
- **Format**: Natural language description
- **Content**: 
  - Character info (Ash Ketchum persona)
  - Pokemon party status
  - Inventory state  
  - Location description
  - Recent actions/dialogue
- **Length**: 100-500 characters for rich context

### `question` (str)
- **Required**: Task prompt for the VLM
- **Standard**: "Analyze the 4-frame sequence and determine the optimal next action."
- **Alternative**: Context-specific questions for different scenarios

### `output` (str)
- **Required**: JSON string with button response
- **Format**: Escaped JSON string
- **Schema**:
  ```json
  {
    "button": "action_name",
    "reasoning": "brief_explanation", 
    "context": "scene_type",
    "scene_description": "detailed_scene_info"
  }
  ```

## Output JSON Schema

### `button` (str)
Valid actions:
- **Movement**: `"up"`, `"down"`, `"left"`, `"right"`
- **Interaction**: `"a"`, `"b"` 
- **Menu**: `"start"`, `"select"`

### `reasoning` (str)
Brief explanation (2-10 words):
- `"clear_path_east"` - No obstacles, move right
- `"npc_interaction"` - Talk to NPC
- `"battle_start"` - Engage wild Pokemon
- `"menu_access"` - Open game menu

### `context` (str)
Scene classification:
- `"navigation"` - Overworld movement
- `"battle"` - Pokemon battle screen
- `"menu"` - Game menus/inventory
- `"dialogue"` - NPC conversation
- `"shop"` - Pokemon Center/Mart

### `scene_description` (str) 
Detailed scene info:
- `"overworld_route_grassy_area"`
- `"pokemon_center_interior"`
- `"battle_wild_pokemon"`
- `"trainer_battle_gym_leader"`

## Example Training Entries

### Navigation Example
```json
{
  "frames": [
    "/data/eevee_v1/route1_001.png",
    "/data/eevee_v1/route1_002.png", 
    "/data/eevee_v1/route1_003.png",
    "/data/eevee_v1/route1_004.png"
  ],
  "context": "Ash exploring Route 1, Pikachu at full health, seeking wild Pokemon encounters for training",
  "question": "Analyze the 4-frame sequence and determine the optimal next action.",
  "output": "{\"button\": \"up\", \"reasoning\": \"tall_grass_ahead\", \"context\": \"navigation\", \"scene_description\": \"route1_grass_wild_pokemon_area\"}"
}
```

### Battle Example  
```json
{
  "frames": [
    "/data/eevee_v1/battle_001.png",
    "/data/eevee_v1/battle_002.png",
    "/data/eevee_v1/battle_003.png", 
    "/data/eevee_v1/battle_004.png"
  ],
  "context": "Pikachu vs wild Pidgey, Pikachu health 80%, Thunder Shock available, type advantage",
  "question": "Analyze the 4-frame sequence and determine the optimal next action.",
  "output": "{\"button\": \"a\", \"reasoning\": \"select_thunder_shock\", \"context\": \"battle\", \"scene_description\": \"wild_battle_pidgey_electric_advantage\"}"
}
```

## Data Conversion Requirements

When converting from Eevee v1 format:

1. **Frame Grouping**: Group sequential screenshots into 4-frame sequences
2. **Path Resolution**: Convert relative paths to absolute paths  
3. **Context Enrichment**: Enhance button-only actions with rich context
4. **JSON Escaping**: Properly escape JSON strings in output field
5. **Validation**: Ensure exactly 4 frames per example

## Training Characteristics

- **Temporal Understanding**: 4-frame sequences teach temporal reasoning
- **Rich Context**: 32K token limit utilized for comprehensive game state
- **Behavioral Cloning**: Learn from expert Eevee v1 gameplay patterns
- **Multi-modal**: Combined vision + language understanding
- **Real-time Ready**: Optimized for ≤5ms inference in Eevee v2