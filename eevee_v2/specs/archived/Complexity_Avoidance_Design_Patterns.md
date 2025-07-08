# Complexity Avoidance Design Patterns
## Proven Patterns for Managing AI System Complexity

### Executive Summary

This document provides proven design patterns extracted from the eevee_v1 → eevee_v2 transformation. These patterns prevent complexity accumulation and maintain system simplicity as AI systems grow in sophistication.

### Core Complexity Avoidance Principles

#### 1. Constraint-First Design
**Principle**: Start with the hardest constraint and design everything around it.

**Eevee Example**: 16.7ms real-time constraint
- **Wrong Approach**: Build features first, optimize later
- **Right Approach**: Design architecture to meet constraint from day one

**Pattern Implementation**:
```python
class ConstraintFirstDesign:
    """Design pattern that enforces constraints at architecture level"""
    
    def __init__(self, primary_constraint: Constraint):
        self.primary_constraint = primary_constraint
        self.components = []
        self.budget_allocator = BudgetAllocator(primary_constraint)
    
    def add_component(self, component: Component, budget_request: float):
        if not self.budget_allocator.can_allocate(budget_request):
            raise ConstraintViolationError(
                f"Component {component} requests {budget_request}ms, "
                f"but only {self.budget_allocator.remaining()}ms available"
            )
        
        self.budget_allocator.allocate(component, budget_request)
        self.components.append(component)
    
    def validate_constraint_compliance(self) -> bool:
        total_used = sum(self.budget_allocator.allocations.values())
        return total_used <= self.primary_constraint.limit
```

#### 2. Single Source of Truth Pattern
**Principle**: Each piece of information has exactly one authoritative source.

**Eevee_v1 Problem**: Game state scattered across multiple classes
- Memory system had its own state
- Agent had cached state
- Controller had separate state
- Visual analyzer had state
- Result: Inconsistency and synchronization complexity

**Eevee_v2 Solution**: Centralized game state
```python
class GameState:
    """Single source of truth for all game information"""
    
    def __init__(self):
        self._state = {}
        self._observers = []
        self._version = 0
    
    def update(self, key: str, value: Any) -> None:
        old_value = self._state.get(key)
        self._state[key] = value
        self._version += 1
        
        # Notify all observers of change
        change = StateChange(key, old_value, value, self._version)
        for observer in self._observers:
            observer.on_state_change(change)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)
    
    def subscribe(self, observer: StateObserver) -> None:
        self._observers.append(observer)

# Components read from single source
class ExecutionLayer:
    def __init__(self, game_state: GameState):
        self.game_state = game_state  # Read-only reference
    
    def get_current_position(self) -> Position:
        return self.game_state.get("player_position")

class MemoryLayer:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        game_state.subscribe(self)  # Listen for changes
    
    def on_state_change(self, change: StateChange) -> None:
        if change.key == "player_position":
            asyncio.create_task(self.update_spatial_memory(change.new_value))
```

#### 3. Error Handling Without Retry Complexity
**Principle**: Handle errors through fallbacks, not retry chains.

**Eevee_v1 Problem**: Complex retry logic for every API call
```python
# WRONG: Complex retry chains
async def call_api_with_retries(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            for provider in ["gemini", "openai", "anthropic"]:
                try:
                    return await call_provider(provider, prompt)
                except ProviderError:
                    continue
            raise AllProvidersFailedError()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await exponential_backoff(attempt)
    # Result: Unpredictable latency, complex error states
```

**Eevee_v2 Solution**: Fallback chain with known latencies
```python
class FallbackChain:
    """Predictable error handling through fallbacks"""
    
    def __init__(self):
        self.fallbacks = [
            CachedActionFallback(),     # 1ms
            PatternMatchFallback(),     # 3ms
            SafeExplorationFallback(),  # 2ms
            EmergencyStopFallback()     # 0.1ms
        ]
    
    async def execute(self, context: GameContext) -> Action:
        for fallback in self.fallbacks:
            try:
                action = await fallback.execute(context)
                if action.confidence > fallback.minimum_confidence:
                    return action
            except Exception as e:
                logging.warning(f"Fallback {fallback} failed: {e}")
                continue
        
        # Final fallback always succeeds
        return Action.SAFE_STOP

class CachedActionFallback:
    """Always succeeds if cache has any relevant action"""
    
    minimum_confidence = 0.3
    
    async def execute(self, context: GameContext) -> Action:
        cached_action = self.cache.get_similar_context(context)
        if cached_action:
            return cached_action.with_confidence(0.4)
        raise NoActionAvailableError()
```

#### 4. Template Management Without Configuration Hell
**Principle**: Compose prompts from small, testable pieces.

**Eevee_v1 Problem**: Monolithic prompt templates
- 500+ line prompt files
- Complex variable substitution
- Difficult to test individual components
- A/B testing required full prompt replacement

**Eevee_v2 Solution**: Compositional prompt system
```python
class PromptComposer:
    """Compose prompts from small, testable components"""
    
    def __init__(self):
        self.components = {
            "system_role": SystemRoleComponent(),
            "game_context": GameContextComponent(),
            "visual_description": VisualDescriptionComponent(),
            "task_instruction": TaskInstructionComponent(),
            "output_format": OutputFormatComponent()
        }
    
    def compose(self, task_type: str, context: Dict[str, Any]) -> str:
        template = self.get_template_for_task(task_type)
        
        rendered_components = {}
        for component_name in template.required_components:
            component = self.components[component_name]
            rendered_components[component_name] = component.render(context)
        
        return template.render(rendered_components)

class SystemRoleComponent:
    """Small, testable prompt component"""
    
    template = "You are an AI playing Pokemon. Your goal is to {objective}."
    
    def render(self, context: Dict[str, Any]) -> str:
        return self.template.format(
            objective=context.get("current_objective", "explore the world")
        )
    
    def test_render(self):
        """Component is easily testable"""
        context = {"current_objective": "reach the Pokemon Center"}
        result = self.render(context)
        assert "Pokemon Center" in result
        return result

# A/B test individual components
class ABTestableComponent:
    def __init__(self):
        self.variants = {
            "concise": "Analyze the game screen briefly.",
            "detailed": "Provide a detailed analysis of the game screen, including all visible elements.",
            "strategic": "Analyze the game screen with focus on strategic opportunities."
        }
        self.current_variant = "concise"
    
    def render(self, context: Dict[str, Any]) -> str:
        return self.variants[self.current_variant]
    
    def set_variant(self, variant: str) -> None:
        if variant in self.variants:
            self.current_variant = variant
```

#### 5. Decision Pipeline Simplification
**Principle**: Linear pipeline with clear handoffs, not complex decision trees.

**Eevee_v1 Problem**: Complex decision logic
```python
# WRONG: Complex decision tree
def make_decision(game_state):
    if game_state.health < 20:
        if game_state.has_healing_items:
            if game_state.in_safe_location:
                return use_healing_item()
            else:
                if game_state.can_escape_battle:
                    return escape_battle()
                else:
                    return fight_defensively()
        else:
            if game_state.pokemon_center_nearby:
                return navigate_to_pokemon_center()
            else:
                return find_healing_items()
    elif game_state.in_battle:
        # ... more complex logic
```

**Eevee_v2 Solution**: Pipeline with clear stages
```python
class DecisionPipeline:
    """Linear decision pipeline with clear responsibilities"""
    
    def __init__(self):
        self.stages = [
            EmergencyStage(),      # Handle critical situations
            BattleStage(),         # Handle battle-specific decisions
            NavigationStage(),     # Handle movement decisions
            ExplorationStage()     # Handle exploration decisions
        ]
    
    async def make_decision(self, context: GameContext) -> Decision:
        for stage in self.stages:
            if stage.can_handle(context):
                decision = await stage.process(context)
                if decision.confidence > stage.confidence_threshold:
                    return decision
        
        # Fallback: safe exploration
        return Decision(action="explore_safely", confidence=0.5)

class EmergencyStage:
    """Handle only critical, high-priority situations"""
    
    confidence_threshold = 0.8
    
    def can_handle(self, context: GameContext) -> bool:
        return (context.health_percentage < 0.2 or 
                context.in_danger or 
                context.stuck_for_turns > 5)
    
    async def process(self, context: GameContext) -> Decision:
        if context.health_percentage < 0.2:
            return Decision(action="seek_healing", confidence=0.9)
        elif context.stuck_for_turns > 5:
            return Decision(action="backtrack", confidence=0.8)
        else:
            return Decision(action="escape_danger", confidence=0.85)
```

### Advanced Complexity Management Patterns

#### 6. The Circuit Breaker Pattern for AI Systems
**Principle**: Prevent cascading failures by failing fast and providing fallbacks.

**Implementation for AI API Calls**:
```python
class AICircuitBreaker:
    """Prevent AI API failures from cascading through system"""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
        self.fallback_model = "cached_patterns"
    
    async def call_ai_with_protection(self, prompt: str, image: str = None) -> AIResponse:
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                # Use fallback instead of AI
                return self.fallback_response(prompt, image)
        
        try:
            response = await self.call_ai_api(prompt, image)
            
            # Success: reset circuit breaker
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            
            return response
            
        except AIAPIException as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            # Always provide fallback response
            return self.fallback_response(prompt, image)
    
    def fallback_response(self, prompt: str, image: str = None) -> AIResponse:
        """Deterministic fallback that always works"""
        if "health" in prompt.lower() and "low" in prompt.lower():
            return AIResponse(action="seek_healing", confidence=0.6)
        elif "battle" in prompt.lower():
            return AIResponse(action="attack", confidence=0.5)
        else:
            return AIResponse(action="explore", confidence=0.4)
```

#### 7. The Strategy Cache Pattern
**Principle**: Cache strategic decisions to avoid repeated expensive computation.

**Multi-Level Strategy Caching**:
```python
class StrategyCache:
    """Multi-level caching for strategic decisions"""
    
    def __init__(self):
        self.immediate_cache = {}  # Exact matches, O(1)
        self.pattern_cache = LRUCache(maxsize=1000)  # Similar patterns
        self.scenario_cache = {}  # High-level scenarios
        self.similarity_threshold = 0.8
    
    def get_strategy(self, context: GameContext) -> Optional[Strategy]:
        # Level 1: Exact context match
        exact_key = self._hash_context(context)
        if exact_key in self.immediate_cache:
            return self.immediate_cache[exact_key]
        
        # Level 2: Similar pattern match
        similar_strategy = self._find_similar_pattern(context)
        if similar_strategy and similar_strategy.confidence > self.similarity_threshold:
            # Promote to immediate cache
            self.immediate_cache[exact_key] = similar_strategy
            return similar_strategy
        
        # Level 3: Scenario-based fallback
        scenario_key = self._get_scenario_key(context)
        if scenario_key in self.scenario_cache:
            return self.scenario_cache[scenario_key]
        
        return None
    
    def store_strategy(self, context: GameContext, strategy: Strategy) -> None:
        exact_key = self._hash_context(context)
        scenario_key = self._get_scenario_key(context)
        
        # Store at all levels
        self.immediate_cache[exact_key] = strategy
        self.pattern_cache[exact_key] = strategy
        self.scenario_cache[scenario_key] = strategy
    
    def _hash_context(self, context: GameContext) -> str:
        """Create hash key for exact matching"""
        return hashlib.md5(
            f"{context.player_position}_{context.game_screen_hash}_{context.current_menu}"
            .encode()
        ).hexdigest()
    
    def _get_scenario_key(self, context: GameContext) -> str:
        """Create high-level scenario key"""
        return f"{context.current_area}_{context.primary_objective}_{context.health_status}"
```

#### 8. The Command Pattern for Undoable Actions
**Principle**: Make all actions undoable to enable safe experimentation.

**Undoable Action System**:
```python
class UndoableAction(ABC):
    """Base class for all undoable actions"""
    
    @abstractmethod
    async def execute(self, game_state: GameState) -> ActionResult:
        pass
    
    @abstractmethod
    async def undo(self, game_state: GameState) -> ActionResult:
        pass
    
    @abstractmethod
    def can_undo(self) -> bool:
        pass

class MovementAction(UndoableAction):
    """Undoable movement action"""
    
    def __init__(self, direction: str):
        self.direction = direction
        self.previous_position = None
    
    async def execute(self, game_state: GameState) -> ActionResult:
        self.previous_position = game_state.get("player_position")
        result = await game_state.controller.move(self.direction)
        return result
    
    async def undo(self, game_state: GameState) -> ActionResult:
        if self.previous_position is None:
            raise UndoError("No previous position recorded")
        
        # Calculate reverse direction
        reverse_direction = self._get_reverse_direction(self.direction)
        result = await game_state.controller.move(reverse_direction)
        return result
    
    def can_undo(self) -> bool:
        return self.previous_position is not None

class ActionManager:
    """Manages undoable actions with automatic rollback"""
    
    def __init__(self, max_history: int = 10):
        self.action_history = collections.deque(maxlen=max_history)
        self.rollback_in_progress = False
    
    async def execute_action(self, action: UndoableAction, game_state: GameState) -> ActionResult:
        try:
            result = await action.execute(game_state)
            
            if result.success:
                self.action_history.append(action)
            else:
                # Action failed, attempt automatic rollback
                await self.rollback_failed_action(action, game_state)
            
            return result
            
        except Exception as e:
            # Exception during execution, attempt rollback
            await self.rollback_failed_action(action, game_state)
            raise
    
    async def rollback_failed_action(self, action: UndoableAction, game_state: GameState) -> None:
        if action.can_undo() and not self.rollback_in_progress:
            self.rollback_in_progress = True
            try:
                await action.undo(game_state)
            except Exception as rollback_error:
                logging.error(f"Rollback failed: {rollback_error}")
            finally:
                self.rollback_in_progress = False
```

#### 9. The Observer Pattern for Loose Coupling
**Principle**: Use events to decouple components instead of direct method calls.

**Event-Driven Architecture**:
```python
class GameEventBus:
    """Central event bus for loose coupling between components"""
    
    def __init__(self):
        self.subscribers = {}
        self.event_history = collections.deque(maxlen=1000)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: GameEvent) -> None:
        self.event_history.append(event)
        
        if event.type in self.subscribers:
            # Publish to all subscribers asynchronously
            tasks = []
            for handler in self.subscribers[event.type]:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            
            # Wait for all handlers, but don't let one failure stop others
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logging.error(f"Event handler {i} failed: {result}")

# Components are loosely coupled through events
class MovementComponent:
    def __init__(self, event_bus: GameEventBus):
        self.event_bus = event_bus
        event_bus.subscribe("player_moved", self.on_player_moved)
    
    async def move_player(self, direction: str) -> None:
        # Execute movement
        success = await self.controller.move(direction)
        
        # Publish event - don't directly call other components
        event = GameEvent(
            type="player_moved",
            data={"direction": direction, "success": success},
            timestamp=time.time()
        )
        await self.event_bus.publish(event)
    
    async def on_player_moved(self, event: GameEvent) -> None:
        # Handle movement-related logic
        if event.data["success"]:
            await self.update_position_tracking(event.data["direction"])

class MemoryComponent:
    def __init__(self, event_bus: GameEventBus):
        self.event_bus = event_bus
        event_bus.subscribe("player_moved", self.on_player_moved)
        event_bus.subscribe("battle_started", self.on_battle_started)
    
    async def on_player_moved(self, event: GameEvent) -> None:
        # Update spatial memory without tight coupling to movement component
        await self.update_spatial_memory(event.data)
```

#### 10. The State Machine Pattern for Complex Logic
**Principle**: Model complex behavior as explicit state machines rather than implicit if/else chains.

**Game State Machine**:
```python
class GameStateMachine:
    """Explicit state machine for complex game logic"""
    
    def __init__(self):
        self.current_state = ExplorationState()
        self.state_history = []
        self.context = GameContext()
    
    async def transition_to(self, new_state: GameState) -> None:
        # Allow current state to clean up
        await self.current_state.on_exit(self.context)
        
        # Record transition
        self.state_history.append(self.current_state)
        
        # Transition to new state
        self.current_state = new_state
        await self.current_state.on_enter(self.context)
    
    async def process_event(self, event: GameEvent) -> None:
        next_state = await self.current_state.handle_event(event, self.context)
        
        if next_state and next_state != self.current_state:
            await self.transition_to(next_state)

class ExplorationState(GameState):
    """State for normal exploration behavior"""
    
    async def handle_event(self, event: GameEvent, context: GameContext) -> Optional[GameState]:
        if event.type == "battle_started":
            return BattleState()
        elif event.type == "low_health":
            return HealingState()
        elif event.type == "objective_completed":
            return ObjectiveSelectionState()
        else:
            # Stay in current state
            return None
    
    async def on_enter(self, context: GameContext) -> None:
        context.set_behavior_mode("exploration")
        await context.event_bus.publish(GameEvent("exploration_started"))
    
    async def on_exit(self, context: GameContext) -> None:
        await context.save_exploration_progress()

class BattleState(GameState):
    """State for battle-specific behavior"""
    
    async def handle_event(self, event: GameEvent, context: GameContext) -> Optional[GameState]:
        if event.type == "battle_ended":
            if context.health_percentage < 0.3:
                return HealingState()
            else:
                return ExplorationState()
        elif event.type == "pokemon_fainted":
            return PokemonManagementState()
        else:
            return None
```

### Testing Patterns for Complex AI Systems

#### 11. The Mock Environment Pattern
**Principle**: Test AI logic without real game dependencies.

**Deterministic Test Environment**:
```python
class MockGameEnvironment:
    """Deterministic environment for testing AI logic"""
    
    def __init__(self):
        self.game_state = {
            "player_position": (10, 10),
            "health": 100,
            "current_area": "test_area",
            "inventory": {"potion": 3, "pokeball": 10}
        }
        self.action_log = []
        self.deterministic_responses = {}
    
    def set_response(self, action: str, response: Dict[str, Any]) -> None:
        """Set deterministic response for testing"""
        self.deterministic_responses[action] = response
    
    async def execute_action(self, action: str) -> ActionResult:
        self.action_log.append(action)
        
        if action in self.deterministic_responses:
            response = self.deterministic_responses[action]
            self.game_state.update(response.get("state_changes", {}))
            return ActionResult(
                success=response.get("success", True),
                message=response.get("message", ""),
                new_state=self.game_state.copy()
            )
        
        # Default response
        return ActionResult(success=True, message="Mock action", new_state=self.game_state)

# Test AI behavior in isolation
async def test_healing_behavior():
    env = MockGameEnvironment()
    ai = EeveeAgent(environment=env)
    
    # Set up test scenario
    env.game_state["health"] = 15  # Low health
    env.set_response("use_potion", {
        "success": True,
        "state_changes": {"health": 65},
        "message": "Health restored"
    })
    
    # Test AI decision
    decision = await ai.make_decision(env.game_state)
    
    # Verify correct behavior
    assert decision.action == "use_potion"
    assert "healing" in decision.reasoning.lower()
    
    # Execute and verify state change
    result = await env.execute_action(decision.action)
    assert env.game_state["health"] == 65
```

### Complexity Metrics and Monitoring

#### 12. The Complexity Budget Pattern
**Principle**: Track and limit complexity growth with measurable metrics.

**Complexity Monitoring System**:
```python
class ComplexityMonitor:
    """Monitor and enforce complexity budgets"""
    
    def __init__(self):
        self.complexity_budgets = {
            "cyclomatic_complexity": {"budget": 10, "current": 0},
            "file_line_count": {"budget": 500, "current": 0},
            "class_responsibility_count": {"budget": 3, "current": 0},
            "dependency_depth": {"budget": 4, "current": 0},
            "api_surface_area": {"budget": 20, "current": 0}
        }
        self.violations = []
    
    def measure_class_complexity(self, cls) -> ComplexityReport:
        """Measure complexity of a class"""
        report = ComplexityReport()
        
        # Count methods (responsibility count)
        method_count = len([m for m in dir(cls) if not m.startswith('_')])
        report.responsibility_count = method_count
        
        # Analyze method complexity
        for method_name in dir(cls):
            if not method_name.startswith('_'):
                method = getattr(cls, method_name)
                if callable(method):
                    complexity = self._analyze_method_complexity(method)
                    report.method_complexities[method_name] = complexity
        
        # Check against budgets
        self._check_budgets(report)
        
        return report
    
    def _check_budgets(self, report: ComplexityReport) -> None:
        """Check if complexity exceeds budgets"""
        if report.responsibility_count > self.complexity_budgets["class_responsibility_count"]["budget"]:
            self.violations.append(
                ComplexityViolation(
                    type="class_responsibility_count",
                    current=report.responsibility_count,
                    budget=self.complexity_budgets["class_responsibility_count"]["budget"],
                    suggestion="Consider splitting class into smaller, focused classes"
                )
            )
        
        max_method_complexity = max(report.method_complexities.values()) if report.method_complexities else 0
        if max_method_complexity > self.complexity_budgets["cyclomatic_complexity"]["budget"]:
            self.violations.append(
                ComplexityViolation(
                    type="cyclomatic_complexity",
                    current=max_method_complexity,
                    budget=self.complexity_budgets["cyclomatic_complexity"]["budget"],
                    suggestion="Simplify complex methods using extraction or state machines"
                )
            )
```

### Implementation Checklist

#### Design Phase
- [ ] Identify primary constraint and design around it
- [ ] Define single sources of truth for all data
- [ ] Plan fallback chains instead of retry logic
- [ ] Design compositional templates/prompts
- [ ] Plan linear decision pipelines

#### Implementation Phase
- [ ] Implement circuit breakers for external dependencies
- [ ] Create multi-level caching strategies
- [ ] Add undoable action support
- [ ] Use event-driven architecture for loose coupling
- [ ] Implement explicit state machines for complex logic

#### Testing Phase
- [ ] Create mock environments for testing
- [ ] Implement complexity monitoring
- [ ] Measure and enforce complexity budgets
- [ ] Test fallback behaviors
- [ ] Validate performance under constraints

#### Monitoring Phase
- [ ] Track complexity metrics over time
- [ ] Monitor constraint compliance
- [ ] Alert on complexity budget violations
- [ ] Measure fallback usage rates
- [ ] Track system stability metrics

These patterns, extracted from the eevee_v1 complexity hell and eevee_v2 simplification, provide proven approaches for maintaining system simplicity while building sophisticated AI capabilities.