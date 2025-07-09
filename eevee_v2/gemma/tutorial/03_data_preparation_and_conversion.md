# Tutorial 03: Data Preparation and Conversion

## Learning Objectives 🎯

By the end of this tutorial, you will:
- Understand Eevee v1's rich session data structure
- Master the data conversion pipeline from sessions to training format
- Create high-quality 2x2 temporal grids from 4-frame sequences
- Apply quality filtering for optimal training data
- Generate comprehensive context prompts for Pokemon gameplay

## Understanding Eevee v1 Data Structure 📊

### Session-Based Architecture

Eevee v1 creates rich gaming sessions with comprehensive AI analysis:

```
eevee/runs/
├── session_20241201_143022/          ← Individual gameplay session
│   ├── session_data.json             ← Core session metadata & turns
│   ├── sshots/                       ← Game screenshots
│   │   ├── step_0001_grid.png       ← Frame captures (240x160)
│   │   ├── step_0002_grid.png
│   │   └── ...
│   ├── step_0001_visual_analysis.txt ← AI visual analysis per frame
│   ├── step_0002_visual_analysis.txt
│   └── ...
└── session_20241201_150845/          ← Another session
    └── ...
```

### Session Data Deep Dive

Let's examine the `session_data.json` structure:

```json
{
  "session_metadata": {
    "session_id": "session_20241201_143022",
    "start_time": "2024-12-01T14:30:22.123456",
    "end_time": "2024-12-01T14:45:33.789012",
    "total_turns": 145,
    "successful_turns": 127,
    "success_rate": 0.876,
    "session_goal": "Navigate to Pokemon Center and heal party",
    "game_version": "Pokemon Emerald",
    "ai_model": "gemini-2.0-flash-exp"
  },
  "turns": [
    {
      "turn": 1,
      "timestamp": "2024-12-01T14:30:22.123456",
      "screenshot_path": "sshots/step_0001_grid.png",
      "ai_analysis": {
        "parsed_json": {
          "button_presses": ["right"],
          "reasoning": "Player character can move right towards the Pokemon Center visible in the distance",
          "observations": "Character is standing on Route 103, Pokemon Center visible to the east",
          "context_detected": "overworld_navigation",
          "confidence": "high",
          "scene_description": "Outdoor route with clear path eastward"
        }
      },
      "template_used": "eevee_pokemon_overworld_v3",
      "template_version": "1.2.1",
      "action_result": "success"
    }
  ]
}
```

### Visual Analysis Integration

Each frame has detailed visual analysis:

```
step_0001_visual_analysis.txt:
{
  "frame_analysis": {
    "scene_type": "overworld",
    "location": "Route 103",
    "player_position": {"x": 120, "y": 80},
    "interactive_elements": [
      {"type": "pokemon_center", "position": {"x": 200, "y": 85}, "accessible": true},
      {"type": "tall_grass", "position": {"x": 160, "y": 90}, "accessible": true}
    ],
    "ui_elements": {
      "health_visible": false,
      "menu_open": false,
      "dialog_active": false
    },
    "movement_options": ["up", "down", "left", "right"],
    "recommended_action": "right",
    "confidence_score": 0.92
  }
}
```

## The Conversion Pipeline 🔄

### Overview

Our conversion process transforms Eevee v1 sessions into training-ready 2x2 grids:

```
Eevee v1 Sessions → 4-Frame Sequences → 2x2 Grids → Training Data
     │                    │                 │             │
 Rich Context       Temporal Logic     Spatial Layout   JSON Actions
```

### Step 1: Session Discovery and Loading

```python
class EeveeSessionLoader:
    """Loads and processes Eevee v1 session data."""
    
    def discover_sessions(self) -> List[Path]:
        """Find all valid session directories with session_data.json."""
        session_dirs = []
        
        for session_dir in self.runs_dir.glob("session_*"):
            if session_dir.is_dir():
                session_data_file = session_dir / "session_data.json"
                if session_data_file.exists():
                    session_dirs.append(session_dir)
        
        return sorted(session_dirs)
    
    def load_session_data(self, session_dir: Path) -> Dict:
        """Load and validate session data."""
        try:
            with open(session_dir / "session_data.json", 'r') as f:
                session_data = json.load(f)
            
            # Validate required fields
            required_fields = ["session_metadata", "turns"]
            if not all(field in session_data for field in required_fields):
                return None
                
            return session_data
        except Exception as e:
            logger.warning(f"Failed to load {session_dir}: {e}")
            return None
```

### Step 2: Quality Filtering

Not all sessions are suitable for training. We apply rigorous quality filters:

```python
class QualityFilter:
    """Filters sessions and sequences based on quality metrics."""
    
    def filter_sessions(self, sessions_data: List[Tuple]) -> List[Tuple]:
        """Filter sessions based on success rate and confidence."""
        filtered = []
        
        for session_data, session_dir in sessions_data:
            metadata = session_data["session_metadata"]
            
            # Success rate filter
            success_rate = metadata.get("success_rate", 0.0)
            if success_rate < self.min_success_rate:
                continue
            
            # Turn count filter (need enough data)
            total_turns = metadata.get("total_turns", 0)
            if total_turns < 20:  # Minimum viable session length
                continue
                
            # Confidence analysis
            high_confidence_turns = sum(
                1 for turn in session_data["turns"]
                if turn.get("ai_analysis", {}).get("parsed_json", {}).get("confidence") == "high"
            )
            
            if high_confidence_turns / total_turns < 0.6:  # 60% high confidence minimum
                continue
                
            filtered.append((session_data, session_dir))
        
        return filtered
```

### Step 3: Temporal Sequence Creation

Convert sessions into 4-frame temporal sequences:

```python
class SequenceCreator:
    """Creates 4-frame temporal sequences from session data."""
    
    def create_sequences(self, session_data: Dict, session_dir: Path, 
                        loader: EeveeSessionLoader) -> List[Dict]:
        """Create overlapping 4-frame sequences from session turns."""
        sequences = []
        turns = session_data["turns"]
        
        # Create overlapping sequences (stride=2 for 50% overlap)
        for i in range(0, len(turns) - 3, 2):
            sequence_turns = turns[i:i+4]
            
            # Validate temporal consistency
            if not self._validate_temporal_sequence(sequence_turns):
                continue
                
            # Build frame paths
            frames = []
            for turn in sequence_turns:
                screenshot_path = self._resolve_screenshot_path(turn, session_dir)
                if screenshot_path and screenshot_path.exists():
                    frames.append(str(screenshot_path))
                else:
                    break  # Skip incomplete sequences
            
            if len(frames) == 4:
                # Create rich training example
                sequence = self._build_training_example(
                    frames, sequence_turns, session_data, session_dir, loader
                )
                sequences.append(sequence)
        
        return sequences
    
    def _validate_temporal_sequence(self, turns: List[Dict]) -> bool:
        """Ensure turns form a valid temporal sequence."""
        
        # Check timestamp ordering
        timestamps = [turn.get("timestamp") for turn in turns]
        if any(ts is None for ts in timestamps):
            return False
            
        # Parse timestamps
        parsed_times = []
        for ts in timestamps:
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                parsed_times.append(dt)
            except:
                return False
        
        # Check temporal order and spacing
        for i in range(1, len(parsed_times)):
            time_diff = (parsed_times[i] - parsed_times[i-1]).total_seconds()
            if time_diff <= 0 or time_diff > 30:  # Max 30 seconds between frames
                return False
        
        return True
```

### Step 4: Rich Context Generation

The secret sauce - creating comprehensive context using Eevee v1's successful patterns:

```python
def _build_rich_context(self, pokemon_context: str, location_context: str,
                       ai_analysis: Dict[str, Any], session_data: Dict[str, Any],
                       target_turn: Dict[str, Any]) -> str:
    """Build comprehensive 32K context using successful Eevee v1 patterns."""
    
    session_goal = session_data["session_metadata"].get("session_goal", "Complete Pokemon objectives")
    template_used = target_turn.get("template_used", "unknown")
    reasoning = ai_analysis.get("reasoning", "Analyzing game state")
    observations = ai_analysis.get("observations", "Observing environment")
    confidence = ai_analysis.get("confidence", "medium")
    
    rich_context = f"""🎮 You are ASH KETCHUM with incredible memory and learning abilities.

**CURRENT MISSION:** {session_goal}

**VISUAL CONTEXT:**
- Location: {location_context}
- Observations: {observations}
- Confidence Level: {confidence}

**STRATEGIC CONTEXT:**
- Template Strategy: {template_used}
- AI Reasoning Chain: {reasoning}
- Pokemon Context: {pokemon_context}

**TEMPORAL ANALYSIS INSTRUCTIONS:**
You receive a 2x2 SPATIAL GRID showing 4 consecutive game frames:
┌─────────┬─────────┐
│ Frame 1 │ Frame 2 │  ← Top row: earlier moments
│ (t=0)   │ (t=1)   │
├─────────┼─────────┤
│ Frame 3 │ Frame 4 │  ← Bottom row: later moments  
│ (t=2)   │ (t=3)   │
└─────────┴─────────┘

**ANALYSIS APPROACH:**
1. Read temporally: TOP-LEFT → TOP-RIGHT → BOTTOM-LEFT → BOTTOM-RIGHT
2. Track movement: Compare character positions across frames
3. Identify changes: Note environmental and UI state evolution
4. Predict action: Consider the temporal progression shown

**ACTION GENERATION:**
Respond with JSON containing:
- button: Next action (up/down/left/right/a/b/start/select)
- reasoning: Brief explanation of choice
- context: Scene type (navigation/battle/menu/dialogue/shop)
- scene_description: Detailed current scene analysis
- temporal_analysis: What progression you observed

**POKEMON EXPERTISE:**
As Ash Ketchum, you have deep knowledge of:
- Pokemon types, moves, and battle strategies
- Route layouts and navigation paths
- Item usage and menu navigation
- NPC interaction patterns
- Optimal grinding and training locations

**CURRENT GAME STATE:**
{pokemon_context}

Remember: You're analyzing the FINAL frame (bottom-right) to determine the next action, but use the full temporal sequence to understand the current situation and movement patterns."""
    
    return rich_context
```

## Grid Creation Process 🎨

### The 2x2 Grid Approach

Converting 4 frames into a single spatial grid:

```python
def create_frame_grid(self, frame_paths: List[str], sequence_id: str) -> str:
    """Create a 2x2 grid from 4 frames with temporal labels."""
    
    # Standard Pokemon frame size (Game Boy Advance)
    self.frame_size = (240, 160)
    self.grid_size = (480, 320)  # 2x2 arrangement
    
    # Load frames
    frames = []
    for frame_path in frame_paths:
        if Path(frame_path).exists():
            frame = Image.open(frame_path).convert("RGB")
            frame = frame.resize(self.frame_size, Image.Resampling.LANCZOS)
        else:
            # Create placeholder for missing frames
            frame = Image.new("RGB", self.frame_size, (64, 64, 64))
        frames.append(frame)
    
    # Create grid canvas
    grid_image = Image.new("RGB", self.grid_size, (32, 32, 32))
    
    # Position frames in temporal order
    positions = [
        (0, 0),                           # Frame 1: Top-left (t=0)
        (self.frame_size[0], 0),          # Frame 2: Top-right (t=1)
        (0, self.frame_size[1]),          # Frame 3: Bottom-left (t=2)
        (self.frame_size[0], self.frame_size[1])  # Frame 4: Bottom-right (t=3)
    ]
    
    # Paste frames with borders
    for frame, pos in zip(frames, positions):
        # Add subtle border for frame separation
        bordered_frame = self._add_border(frame)
        grid_image.paste(bordered_frame, pos)
    
    # Add temporal labels
    if self.add_labels:
        self._add_temporal_labels(grid_image)
    
    # Save grid image
    grid_path = self.grid_images_dir / f"grid_{sequence_id}.png"
    grid_image.save(grid_path, "PNG", optimize=True)
    
    return str(grid_path)
```

### Visual Enhancement

Adding temporal labels to help the model understand sequence order:

```python
def _add_temporal_labels(self, grid_image: Image.Image) -> None:
    """Add temporal labels (t=0, t=1, t=2, t=3) to grid quadrants."""
    
    draw = ImageDraw.Draw(grid_image)
    
    # Label configurations
    labels = ["t=0", "t=1", "t=2", "t=3"]
    positions = [
        (5, 5),                                    # Top-left
        (self.frame_size[0] + 5, 5),              # Top-right
        (5, self.frame_size[1] + 5),              # Bottom-left
        (self.frame_size[0] + 5, self.frame_size[1] + 5)  # Bottom-right
    ]
    
    # Draw labels with shadow for visibility
    for label, pos in zip(labels, positions):
        # Shadow
        draw.text((pos[0] + 1, pos[1] + 1), label, fill=(0, 0, 0))
        # Main text
        draw.text(pos, label, fill=(255, 255, 0))  # Yellow text
```

## Practical Data Conversion 🛠️

### Running the Full Pipeline

```bash
# Complete conversion from Eevee v1 to grid training data
python scripts/convert_eevee_data_v2.py \
    --eevee_runs_dir /path/to/eevee/runs \
    --output_file training_data/pokemon_4frame_dataset.jsonl \
    --min_success_rate 0.8 \
    --min_confidence high \
    --copy_images

# Then convert to 2x2 grids
python scripts/convert_frames_to_grid.py \
    --input training_data/pokemon_4frame_dataset.jsonl \
    --output_dir training_data \
    --border-width 2
```

### Alternative: Direct Grid Creation

```bash
# New feature: Create grids directly from Eevee v1 data
python scripts/convert_eevee_data_v2.py \
    --eevee_runs_dir /path/to/eevee/runs \
    --output_file training_data/pokemon_grid_dataset.jsonl \
    --min_success_rate 0.8 \
    --create_grids \
    --copy_images
```

### Output Validation

The conversion process generates comprehensive validation data:

```json
// conversion_summary.json
{
  "conversion_time": "2024-12-08T10:30:45.123456",
  "input_directory": "/path/to/eevee/runs",
  "sessions_discovered": 101,
  "sessions_processed": 87,
  "sequences_created": 1247,
  "sequences_output": 671,
  "quality_filters": {
    "min_success_rate": 0.8,
    "min_confidence": "high"
  },
  "sample_sequence": {
    "image": "grid_images/grid_000001.png",
    "context": "🎮 You are ASH KETCHUM...",
    "question": "Looking at this 2x2 temporal grid...",
    "output": "{\"button\": \"right\", \"reasoning\": \"clear_path\"}"
  }
}
```

## Data Quality Analysis 📈

### Quality Metrics

Understanding what makes good training data:

```python
def analyze_data_quality(dataset_path: str):
    """Analyze the quality and characteristics of converted data."""
    
    # Load dataset
    samples = []
    with open(dataset_path, 'r') as f:
        for line in f:
            samples.append(json.loads(line.strip()))
    
    print(f"📊 Dataset Analysis: {len(samples)} samples")
    
    # Action distribution
    actions = []
    for sample in samples:
        try:
            output = json.loads(sample["output"])
            actions.append(output.get("button", "unknown"))
        except:
            actions.append("parse_error")
    
    from collections import Counter
    action_counts = Counter(actions)
    
    print("🎮 Action Distribution:")
    for action, count in action_counts.most_common():
        percentage = count / len(samples) * 100
        print(f"  {action}: {count} ({percentage:.1f}%)")
    
    # Context length analysis
    context_lengths = [len(sample["context"]) for sample in samples]
    avg_context = sum(context_lengths) / len(context_lengths)
    
    print(f"\n📝 Context Analysis:")
    print(f"  Average length: {avg_context:.0f} characters")
    print(f"  Max length: {max(context_lengths)} characters")
    print(f"  Min length: {min(context_lengths)} characters")
    
    # Session diversity
    session_ids = set()
    for sample in samples:
        if "metadata" in sample:
            session_ids.add(sample["metadata"].get("session_id", "unknown"))
    
    print(f"\n🎯 Session Diversity:")
    print(f"  Unique sessions: {len(session_ids)}")
    print(f"  Samples per session: {len(samples) / len(session_ids):.1f}")
    
    return {
        "total_samples": len(samples),
        "action_distribution": dict(action_counts),
        "context_stats": {
            "avg_length": avg_context,
            "max_length": max(context_lengths),
            "min_length": min(context_lengths)
        },
        "session_diversity": len(session_ids)
    }

# Run analysis
stats = analyze_data_quality("training_data/pokemon_grid_dataset.jsonl")
```

### Expected Quality Benchmarks

Good Pokemon training data should have:

```
✅ Action Balance:
   - Navigation: 60-70% (up/down/left/right)
   - Interaction: 20-25% (a/b buttons)
   - Menu: 10-15% (start/select)

✅ Context Richness:
   - Average: 2000-4000 characters
   - Rich game state information
   - Temporal progression descriptions

✅ Session Diversity:
   - 50+ unique sessions
   - Various Pokemon scenarios
   - Different game states represented

✅ Confidence Distribution:
   - 70%+ high confidence samples
   - Clear action reasoning
   - Accurate scene descriptions
```

## Troubleshooting Common Issues 🔧

### Issue 1: Missing Screenshots

```python
# Diagnosis
def diagnose_missing_screenshots(session_dir: Path):
    """Identify patterns in missing screenshot files."""
    
    with open(session_dir / "session_data.json") as f:
        session_data = json.load(f)
    
    missing_files = []
    for turn in session_data["turns"]:
        screenshot_path = session_dir / turn.get("screenshot_path", "")
        if not screenshot_path.exists():
            missing_files.append(screenshot_path)
    
    print(f"Missing files: {len(missing_files)}")
    return missing_files

# Solution: Enhanced path resolution
def _resolve_screenshot_path(self, turn: Dict, session_dir: Path) -> Optional[Path]:
    """Try multiple screenshot path formats."""
    
    # Try paths in order of likelihood
    candidates = [
        session_dir / turn.get("screenshot_path", ""),
        session_dir / "sshots" / f"step_{turn['turn']:04d}_grid.png",
        session_dir / f"screenshot_{turn['turn']}.png"
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return None
```

### Issue 2: Temporal Validation Failures

```python
# Common temporal issues and solutions
def fix_temporal_issues():
    """Address common temporal sequence problems."""
    
    issues = {
        "out_of_order_timestamps": {
            "problem": "Timestamps not in chronological order",
            "solution": "Sort turns by timestamp before sequence creation"
        },
        "large_time_gaps": {
            "problem": "More than 30 seconds between frames",
            "solution": "Split into separate sequences at gaps"
        },
        "duplicate_timestamps": {
            "problem": "Multiple turns with same timestamp",
            "solution": "Add microsecond offsets or skip duplicates"
        }
    }
    
    return issues
```

### Issue 3: Grid Quality Problems

```python
# Grid visualization issues
def validate_grid_quality(grid_path: str):
    """Check if grid was created properly."""
    
    grid = Image.open(grid_path)
    
    # Check dimensions
    if grid.size != (480, 320):
        print(f"❌ Wrong grid size: {grid.size}")
        return False
    
    # Check for blank quadrants (indicates missing frames)
    quadrants = [
        grid.crop((0, 0, 240, 160)),      # Top-left
        grid.crop((240, 0, 480, 160)),    # Top-right
        grid.crop((0, 160, 240, 320)),    # Bottom-left
        grid.crop((240, 160, 480, 320))   # Bottom-right
    ]
    
    for i, quad in enumerate(quadrants):
        # Check if quadrant is completely black (missing frame indicator)
        if all(pixel < 10 for pixel in quad.getdata()):
            print(f"❌ Missing frame in quadrant {i+1}")
            return False
    
    print("✅ Grid quality check passed")
    return True
```

## Practical Exercises 🎯

### Exercise 1: Convert Sample Data

```bash
# Create a test conversion with limited data
python scripts/convert_eevee_data_v2.py \
    --eevee_runs_dir /path/to/eevee/runs \
    --output_file training_data/test_grid_dataset.jsonl \
    --create_grids \
    --max_sessions 5 \
    --copy_images

# Analyze the results
python -c "
import json
with open('training_data/test_grid_dataset.jsonl') as f:
    samples = [json.loads(line) for line in f]
print(f'Created {len(samples)} training samples')
print(f'First sample keys: {list(samples[0].keys())}')
"
```

### Exercise 2: Quality Analysis

```python
# Run comprehensive quality analysis
python scripts/analyze_data_quality.py \
    --dataset training_data/test_grid_dataset.jsonl \
    --output_report data_quality_report.json

# Visualize action distribution
python scripts/visualize_data_distribution.py \
    --dataset training_data/test_grid_dataset.jsonl
```

### Exercise 3: Grid Inspection

```python
# Manually inspect generated grids
from PIL import Image
import matplotlib.pyplot as plt

def inspect_grid(grid_path: str):
    """Visually inspect a generated grid."""
    
    grid = Image.open(grid_path)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(grid)
    plt.title(f"2x2 Temporal Grid: {grid_path}")
    plt.axis('off')
    
    # Add quadrant labels
    plt.text(60, 40, "t=0", fontsize=16, color='yellow', weight='bold')
    plt.text(300, 40, "t=1", fontsize=16, color='yellow', weight='bold')
    plt.text(60, 200, "t=2", fontsize=16, color='yellow', weight='bold')
    plt.text(300, 200, "t=3", fontsize=16, color='yellow', weight='bold')
    
    plt.show()

# Inspect first few grids
import glob
grid_files = glob.glob("training_data/grid_images/grid_*.png")[:3]
for grid_file in grid_files:
    inspect_grid(grid_file)
```

## Key Takeaways 💡

1. **Rich Data Structure**: Eevee v1 provides exceptional training data with AI reasoning and visual analysis
2. **Quality First**: Rigorous filtering ensures only high-quality sequences for training
3. **Temporal Preservation**: 2x2 grids maintain temporal information in spatial layout
4. **Context Enhancement**: Comprehensive prompts leverage Eevee v1's successful patterns
5. **Validation Critical**: Multiple validation layers ensure data integrity

## Next Steps 🚀

In **Tutorial 04**, we'll configure training:
- Setting up accelerate for distributed training
- Configuring QLoRA for memory efficiency
- Optimizing hyperparameters for grid training
- Setting up monitoring and logging

### Preparation for Tutorial 04

```bash
# Prepare training configuration
cd /Users/wingston/code/claude-plays-pokemon/eevee_v2/gemma

# Validate data pipeline
python scripts/validate_training.py --test dataset

# Check hardware configuration
python scripts/find_batch_size.py \
    --dataset_path training_data/test_grid_dataset.jsonl \
    --output batch_size_config.json

echo "✅ Ready for Tutorial 04: Training Configuration!"
```

---

**Excellent! You've mastered data conversion. Ready to configure training in Tutorial 04? ⚙️**