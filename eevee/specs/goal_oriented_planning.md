# Goal-Oriented Planning System for Pokemon AI

## Overview
Transform the current flat task execution system into a hierarchical goal-oriented planning system that can decompose high-level objectives into actionable subtasks.

## Current State Analysis

### What We Have
- **Task Executor**: Converts task strings into multi-step execution plans
- **Task Memory**: Neo4j-based system that tracks task execution history and success patterns
- **Goal References**: Prompts use "GOAL: {task}" as context for decision-making
- **Learning System**: Stores successful task patterns and execution history

### What's Missing
- **Goal Hierarchy**: No formal parent-child relationship between goals and subgoals
- **Dynamic Planning**: Goals are static strings, not dynamically generated based on game state
- **Progress Tracking**: No systematic way to track progress through goal hierarchies
- **Goal Generation**: No mechanism to generate new goals based on current state

## Proposed OKR based Goal-Oriented Architecture

### 1. Goal Hierarchy Structure
```
Epic: Defeat Elite Four
├── Story: Complete 8 Gym Badges
│   ├── Chapter: Pewter City Gym (Rock Type)
│   │   ├── Task: Build team to counter Rock types
│   │   │   ├── Subtask: Catch water/grass Pokemon
│   │   │   ├── Subtask: Level up team to 10+
│   │   │   └── Subtask: Stock up on potions
│   │   ├── Task: Navigate to Pewter City
│   │   │   ├── Subtask: Exit Viridian City
│   │   │   ├── Subtask: Travel through Viridian Forest
│   │   │   └── Subtask: Enter Pewter City
│   │   └── Task: Challenge Brock
│   │       ├── Subtask: Heal at Pokemon Center
│   │       ├── Subtask: Navigate to Gym
│   │       └── Subtask: Defeat Brock
│   └── Chapter: Cerulean City Gym (Water Type)
│       └── ... similar structure
└── Story: Build Championship Team
    └── ... team building goals
```

### 2. Goal State Machine
Each goal can be in one of these states:
- **Not Started**: Goal identified but not begun
- **In Progress**: Actively working on this goal
- **Blocked**: Cannot proceed (missing prerequisites)
- **Completed**: Goal achieved
- **Failed**: Goal cannot be completed (need alternative)
- **Deferred**: Postponed for later

### 3. Goal Properties
```python
class Goal:
    id: str
    name: str
    description: str
    type: GoalType  # Epic, Story, Chapter, Task, Subtask
    parent_id: Optional[str]
    children: List[str]
    prerequisites: List[str]  # Other goal IDs that must complete first
    
    # Progress tracking
    state: GoalState
    progress_percentage: float
    attempts: int
    
    # Planning metadata
    estimated_turns: int
    priority: int
    context_requirements: List[str]  # e.g., "must have water pokemon", "need 500+ money"
    
    # Execution
    execution_strategy: str  # Which prompt/approach to use
    success_criteria: Dict  # How to know when complete
    failure_conditions: Dict  # When to abandon and try alternative
```

### 4. Dynamic Goal Generation

#### Goal Templates
Create reusable templates for common goals:
```yaml
heal_at_pokecenter:
  name: "Heal Pokemon at {location} Pokemon Center"
  prerequisites:
    - have_injured_pokemon
    - know_pokecenter_location
  subtasks:
    - navigate_to_building: "Pokemon Center"
    - interact_with_nurse
    - confirm_healing
    - exit_building

catch_pokemon_type:
  name: "Catch {type} type Pokemon"
  prerequisites:
    - have_pokeballs
    - know_spawn_location: "{type}"
  subtasks:
    - navigate_to_area: "{spawn_location}"
    - search_for_pokemon
    - engage_in_battle
    - weaken_pokemon
    - use_pokeball
```

#### Goal Generator Logic
```python
def generate_next_goals(game_state, current_goals, memory):
    """Generate appropriate goals based on current game state"""
    
    # Check major objectives
    if not has_badge("Boulder Badge"):
        if team_average_level < 10:
            return create_goal("level_up_team", target_level=10)
        elif not has_type_advantage("rock"):
            return create_goal("catch_pokemon_type", type="water")
        else:
            return create_goal("challenge_pewter_gym")
    
    # Check immediate needs
    if team_health_percentage < 30:
        return create_goal("heal_at_pokecenter", priority=HIGH)
    
    # Continue with current goal hierarchy
    return get_next_subtask(current_goals)
```

### 5. Integration with Existing System

#### Modify run_eevee.py
```python
# Current
python run_eevee.py --goal "enter the pokecenter and heal your pokemon"

# Proposed additions
python run_eevee.py --epic "defeat_elite_four" --start-chapter "pewter_gym"
python run_eevee.py --goal-hierarchy goals/pewter_gym_plan.yaml
python run_eevee.py --auto-goals  # Let AI generate goals dynamically
```

#### Task Executor Enhancement
- Keep current task executor for leaf-level subtasks
- Add goal decomposition layer above it
- Task executor handles "how", goal planner handles "what" and "when"

#### Memory Integration
- Store goal hierarchies in Neo4j
- Track relationships between goals
- Learn successful goal sequences
- Remember failed approaches to avoid repetition

### 6. Testing Strategy

#### Phase 1: Simple Goal Chains
Test with linear goal sequences:
1. "Enter Pokemon Center" → "Talk to Nurse" → "Heal Pokemon" → "Exit"

#### Phase 2: Branching Goals
Test with conditional paths:
1. "Get to Pewter Gym" → 
   - If blocked by NPC → "Complete side quest"
   - If underleveled → "Train in grass"
   - If ready → "Enter gym"

#### Phase 3: Dynamic Goal Generation
Test with state-based goal creation:
1. System recognizes low health → Generates "heal" goal
2. System sees new area → Generates "explore" goal
3. System detects type disadvantage → Generates "catch counter-type" goal

### 7. Prompting Strategy

#### Goal Decomposition Prompt
```
Given the current goal: {parent_goal}
Current game state: {game_state}
Available resources: {resources}

Break this down into 3-5 subtasks that:
1. Are concrete and measurable
2. Build toward the parent goal
3. Can be executed with current resources
4. Have clear completion criteria

Output as structured JSON with task dependencies.
```

#### Goal Selection Prompt
```
Current active goals: {goals_list}
Game state: {state}
Recent actions: {history}

Select the most appropriate goal to pursue now, considering:
1. Prerequisites met
2. Resource availability  
3. Efficiency (minimize backtracking)
4. Risk/reward balance

Explain your reasoning.
```

### 8. Success Metrics

- **Goal Completion Rate**: % of goals successfully completed
- **Planning Efficiency**: Turns taken vs optimal path
- **Adaptation Success**: % of times system recovers from blocked goals
- **Hierarchy Depth Utilization**: How well system uses full goal tree
- **Dynamic Goal Quality**: Relevance of auto-generated goals

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Define goal data structures
- [ ] Create goal hierarchy parser
- [ ] Implement basic parent-child relationships
- [ ] Add goal state tracking

### Phase 2: Integration (Week 2)
- [ ] Connect to existing task executor
- [ ] Modify prompts to use goal context
- [ ] Update Neo4j schema for goals
- [ ] Create goal visualization tools

### Phase 3: Intelligence (Week 3)
- [ ] Implement goal generator
- [ ] Add goal template system
- [ ] Create goal selection logic
- [ ] Build learning/adaptation system

### Phase 4: Testing & Refinement (Week 4)
- [ ] Test Pewter Gym complete sequence
- [ ] Measure performance improvements
- [ ] Tune goal generation parameters
- [ ] Document best practices

## Open Questions

1. **Goal Persistence**: Should goals persist across sessions or regenerate?
2. **Failure Handling**: How many attempts before abandoning a goal?
3. **Goal Conflicts**: How to handle mutually exclusive goals?
4. **Resource Planning**: Should goals reserve resources (money, items)?
5. **Learning Transfer**: Can goal patterns from one gym apply to others?
6. **Human Override**: How to handle user-injected goals in hierarchy?
7. **Evaluation Loops**: When to re-evaluate goal relevance?

## Next Steps

1. Review and refine this specification
2. Create proof-of-concept for Pewter Gym sequence
3. Design goal description language (YAML/JSON schema)
4. Build goal visualization dashboard
5. Implement basic goal executor wrapper