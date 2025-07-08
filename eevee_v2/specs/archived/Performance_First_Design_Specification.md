# Performance-First Design Specification
## Real-Time AI System Performance Requirements and Patterns

### Executive Summary

This specification defines performance-first design principles for real-time AI systems, extracted from the eevee_v1 performance crisis and eevee_v2 performance solution. The core principle: **Performance is not an optimization problem, it's an architecture problem**.

### Real-Time AI System Requirements

#### 1. Critical Performance Constraints
**Primary Constraint: 60 FPS Real-Time Execution**
- **Frame Budget**: 16.7ms total time per frame
- **AI Budget**: ≤5ms for AI decision making
- **System Budget**: ≤11.7ms for capture, I/O, and overhead
- **Buffer**: Keep 20% margin (13.3ms actual target)

**Constraint Breakdown**:
```
Frame Time Budget (16.7ms):
├── Frame Capture: 2ms (12%)
├── AI Processing: 5ms (30%)
├── Action Execution: 1ms (6%)
├── System Overhead: 2ms (12%)
└── Safety Buffer: 6.7ms (40%)
```

**Performance Tiers**:
- **Critical Path**: ≤5ms (must never exceed)
- **Strategic Path**: 100-500ms (pause-based)
- **Background Path**: 1-30s (async processing)

#### 2. Latency Requirements by Component

**Component Latency Budgets**:
```python
class PerformanceBudgets:
    """Strict performance budgets for each system component"""
    
    BUDGETS = {
        # Critical path (60 FPS)
        "pattern_matching": 2.0,      # Pattern recognition
        "cache_lookup": 1.0,          # Action cache access
        "action_execution": 1.0,      # Button/controller output
        "safety_check": 0.5,          # Safety validation
        "telemetry": 0.5,            # Performance monitoring
        
        # Strategic path (pause-based)
        "vision_analysis": 200.0,     # Deep visual analysis
        "strategic_planning": 200.0,  # Strategic reasoning
        "memory_query": 50.0,         # Knowledge retrieval
        "cache_update": 50.0,         # Strategy cache update
        
        # Background path (async)
        "memory_storage": 5000.0,     # Persistent storage
        "learning_update": 10000.0,   # Model fine-tuning
        "knowledge_sync": 30000.0,    # Full knowledge sync
    }
    
    @classmethod
    def validate_operation(cls, operation: str, elapsed_time: float) -> bool:
        """Validate operation meets performance budget"""
        budget = cls.BUDGETS.get(operation)
        if budget is None:
            return True  # Unknown operation, assume valid
        
        return elapsed_time <= budget
    
    @classmethod
    def get_budget(cls, operation: str) -> float:
        """Get performance budget for operation in milliseconds"""
        return cls.BUDGETS.get(operation, float('inf'))
```

### Multi-Frequency Processing Architecture

#### 1. Frequency-Based Layer Design
**Three-Tier Frequency Architecture**:

```python
class MultiFrequencyProcessor:
    """Process different aspects at different frequencies"""
    
    def __init__(self):
        self.critical_frequency = 60    # 60 FPS
        self.strategic_frequency = 2    # 2 Hz (every 500ms)
        self.background_frequency = 0.1 # 0.1 Hz (every 10s)
        
        self.frame_counter = 0
        self.last_strategic_time = 0
        self.last_background_time = 0
    
    async def process_frame(self, game_state: GameState) -> Action:
        self.frame_counter += 1
        current_time = time.time()
        
        # Critical processing (every frame)
        action = await self.process_critical(game_state)
        
        # Strategic processing (every 30 frames = 500ms)
        if self.frame_counter % 30 == 0:
            asyncio.create_task(self.process_strategic(game_state))
        
        # Background processing (every 600 frames = 10s)
        if self.frame_counter % 600 == 0:
            asyncio.create_task(self.process_background(game_state))
        
        return action
    
    async def process_critical(self, game_state: GameState) -> Action:
        """Critical path: ≤5ms processing"""
        start_time = time.perf_counter()
        
        # Pattern matching (≤2ms)
        pattern = await self.pattern_matcher.match(game_state)
        
        # Cache lookup (≤1ms)
        cached_action = self.action_cache.get(pattern)
        if cached_action:
            return cached_action
        
        # Safe fallback (≤1ms)
        fallback_action = self.fallback_generator.get_safe_action(game_state)
        
        # Performance validation
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5.0:
            self.performance_monitor.log_violation("critical_path", elapsed)
        
        return fallback_action
    
    async def process_strategic(self, game_state: GameState) -> None:
        """Strategic path: pause-based processing"""
        await self.game_controller.pause()
        
        try:
            # Deep analysis (200ms budget)
            analysis = await self.vision_analyzer.analyze(game_state.screenshot)
            
            # Strategic planning (200ms budget)
            strategy = await self.strategic_planner.plan(analysis, game_state)
            
            # Update action cache
            self.action_cache.update(strategy)
            
        finally:
            await self.game_controller.resume()
    
    async def process_background(self, game_state: GameState) -> None:
        """Background path: long-term learning and storage"""
        # Store experience for learning
        experience = Experience.from_game_state(game_state)
        await self.memory_system.store_experience(experience)
        
        # Update knowledge graph
        await self.knowledge_graph.update(experience)
        
        # Trigger learning if enough new data
        if self.should_trigger_learning():
            asyncio.create_task(self.learning_system.update_model())
```

#### 2. Adaptive Frequency Scaling
**Dynamic Performance Adjustment**:

```python
class AdaptiveFrequencyManager:
    """Dynamically adjust processing frequency based on performance"""
    
    def __init__(self):
        self.performance_history = collections.deque(maxlen=300)  # 5 seconds at 60fps
        self.strategic_frequency = 2.0  # Hz
        self.min_strategic_frequency = 0.5  # Hz
        self.max_strategic_frequency = 4.0  # Hz
        
    def adjust_frequencies(self, current_frame_time: float) -> None:
        """Adjust processing frequencies based on performance"""
        self.performance_history.append(current_frame_time)
        
        if len(self.performance_history) < 60:  # Need 1 second of data
            return
        
        # Calculate recent performance metrics
        recent_times = list(self.performance_history)[-60:]  # Last 1 second
        avg_frame_time = sum(recent_times) / len(recent_times)
        p95_frame_time = sorted(recent_times)[int(len(recent_times) * 0.95)]
        
        # Adjust strategic frequency based on performance
        if p95_frame_time > 15.0:  # Close to budget limit
            # Reduce strategic frequency to free up CPU
            self.strategic_frequency = max(
                self.min_strategic_frequency,
                self.strategic_frequency * 0.8
            )
        elif avg_frame_time < 8.0:  # Well under budget
            # Increase strategic frequency for better decisions
            self.strategic_frequency = min(
                self.max_strategic_frequency,
                self.strategic_frequency * 1.1
            )
    
    def get_strategic_interval_frames(self) -> int:
        """Get interval between strategic processing in frames"""
        return int(60 / self.strategic_frequency)  # 60 FPS base
```

### Caching Strategies for AI Systems

#### 1. Multi-Level Caching Architecture
**Hierarchical Cache Design**:

```python
class AISystemCache:
    """Multi-level caching optimized for AI workloads"""
    
    def __init__(self):
        # L1: Immediate action cache (in-memory dict)
        self.l1_cache = {}  # ~100 entries, <1ms access
        
        # L2: Pattern recognition cache (LRU)
        self.l2_cache = LRUCache(maxsize=1000)  # ~1000 entries, <5ms access
        
        # L3: Strategic decision cache (SQLite)
        self.l3_cache = SQLiteCache(
            db_path="strategy_cache.db",
            max_entries=10000
        )  # ~10k entries, <50ms access
        
        # L4: Long-term knowledge cache (Neo4j)
        self.l4_cache = Neo4jCache()  # Unlimited, <200ms access
        
        self.cache_stats = CacheStats()
    
    async def get_action(self, context: GameContext) -> Optional[CachedAction]:
        """Get cached action using hierarchical lookup"""
        context_key = self._hash_context(context)
        
        # L1: Immediate lookup
        if context_key in self.l1_cache:
            self.cache_stats.record_hit("L1")
            return self.l1_cache[context_key]
        
        # L2: Pattern-based lookup
        pattern_key = self._extract_pattern(context)
        l2_action = self.l2_cache.get(pattern_key)
        if l2_action and self._is_applicable(l2_action, context):
            self.cache_stats.record_hit("L2")
            # Promote to L1
            self.l1_cache[context_key] = l2_action
            return l2_action
        
        # L3: Strategic lookup (async)
        l3_action = await self.l3_cache.get_async(context)
        if l3_action:
            self.cache_stats.record_hit("L3")
            # Promote to higher levels
            self.l2_cache[pattern_key] = l3_action
            self.l1_cache[context_key] = l3_action
            return l3_action
        
        # L4: Knowledge-based lookup (async)
        l4_action = await self.l4_cache.get_similar_context(context)
        if l4_action:
            self.cache_stats.record_hit("L4")
            return l4_action
        
        self.cache_stats.record_miss()
        return None
    
    async def store_action(
        self,
        context: GameContext,
        action: Action,
        performance_level: str = "strategic"
    ) -> None:
        """Store action in appropriate cache levels"""
        context_key = self._hash_context(context)
        pattern_key = self._extract_pattern(context)
        
        cached_action = CachedAction(
            action=action,
            context=context,
            timestamp=time.time(),
            performance_level=performance_level
        )
        
        # Store at appropriate levels based on performance
        if performance_level == "critical":
            # Critical actions go in all levels
            self.l1_cache[context_key] = cached_action
            self.l2_cache[pattern_key] = cached_action
            await self.l3_cache.store_async(context, cached_action)
        
        elif performance_level == "strategic":
            # Strategic actions skip L1 but go in L2+
            self.l2_cache[pattern_key] = cached_action
            await self.l3_cache.store_async(context, cached_action)
        
        # Always store in L4 for knowledge building
        await self.l4_cache.store_async(context, cached_action)
```

#### 2. Context-Aware Cache Invalidation
**Smart Cache Management**:

```python
class SmartCacheInvalidator:
    """Intelligent cache invalidation based on context changes"""
    
    def __init__(self, cache: AISystemCache):
        self.cache = cache
        self.context_tracker = ContextTracker()
        self.invalidation_rules = self._build_invalidation_rules()
    
    def _build_invalidation_rules(self) -> List[InvalidationRule]:
        """Define when cached actions become invalid"""
        return [
            InvalidationRule(
                trigger="area_changed",
                invalidate_patterns=["movement_*", "exploration_*"],
                reasoning="Navigation patterns invalid in new area"
            ),
            InvalidationRule(
                trigger="health_critical",
                invalidate_patterns=["combat_*", "exploration_*"],
                reasoning="Priority shifted to survival"
            ),
            InvalidationRule(
                trigger="new_objective",
                invalidate_patterns=["strategic_*"],
                reasoning="Goals changed, strategies invalid"
            ),
            InvalidationRule(
                trigger="time_expired",
                invalidate_age=300,  # 5 minutes
                reasoning="Stale strategies may be outdated"
            )
        ]
    
    async def on_context_change(self, change: ContextChange) -> None:
        """Handle context changes and invalidate relevant cache entries"""
        for rule in self.invalidation_rules:
            if rule.matches(change):
                await self._apply_invalidation_rule(rule, change)
    
    async def _apply_invalidation_rule(
        self,
        rule: InvalidationRule,
        change: ContextChange
    ) -> None:
        """Apply invalidation rule to cache"""
        if rule.invalidate_patterns:
            # Pattern-based invalidation
            for pattern in rule.invalidate_patterns:
                invalidated_count = await self.cache.invalidate_pattern(pattern)
                logging.info(
                    f"Invalidated {invalidated_count} entries matching '{pattern}' "
                    f"due to {change.type}: {rule.reasoning}"
                )
        
        elif rule.invalidate_age:
            # Age-based invalidation
            cutoff_time = time.time() - rule.invalidate_age
            invalidated_count = await self.cache.invalidate_older_than(cutoff_time)
            logging.info(
                f"Invalidated {invalidated_count} entries older than {rule.invalidate_age}s"
            )
```

### Background vs Foreground Processing

#### 1. Processing Priority Classification
**Task Classification System**:

```python
class ProcessingPriorityManager:
    """Classify and route tasks to appropriate processing paths"""
    
    def __init__(self):
        self.task_classifiers = {
            "critical": CriticalTaskClassifier(),
            "strategic": StrategicTaskClassifier(),
            "background": BackgroundTaskClassifier()
        }
        
        self.processing_pools = {
            "critical": CriticalProcessor(),     # Synchronous, <5ms
            "strategic": StrategicProcessor(),   # Pause-based, <500ms
            "background": BackgroundProcessor()  # Async, unlimited time
        }
    
    async def process_task(self, task: AITask) -> TaskResult:
        """Route task to appropriate processor based on priority"""
        priority = self._classify_task(task)
        processor = self.processing_pools[priority]
        
        return await processor.process(task)
    
    def _classify_task(self, task: AITask) -> str:
        """Classify task priority based on content and context"""
        # Safety-critical tasks
        if task.type in ["emergency_stop", "collision_avoidance", "health_critical"]:
            return "critical"
        
        # Real-time decision tasks
        if task.type in ["movement_decision", "immediate_action"]:
            return "critical"
        
        # Planning and analysis tasks
        if task.type in ["strategic_planning", "deep_analysis", "goal_setting"]:
            return "strategic"
        
        # Learning and storage tasks
        if task.type in ["memory_storage", "model_update", "knowledge_sync"]:
            return "background"
        
        # Default to strategic for unknown tasks
        return "strategic"

class CriticalProcessor:
    """Process critical tasks with strict timing guarantees"""
    
    async def process(self, task: AITask) -> TaskResult:
        start_time = time.perf_counter()
        
        try:
            # Use only cached or pre-computed results
            result = await self._process_with_cache_only(task)
            
            # Validate timing constraint
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 5.0:
                raise PerformanceViolationError(
                    f"Critical task took {elapsed:.2f}ms, budget is 5ms"
                )
            
            return result
            
        except Exception as e:
            # Critical tasks must always return something
            return self._get_safe_fallback_result(task)
    
    async def _process_with_cache_only(self, task: AITask) -> TaskResult:
        """Process using only cached/pre-computed data"""
        cached_result = self.cache.get_immediate(task.key)
        if cached_result:
            return cached_result
        
        # Generate minimal safe result
        return self._generate_minimal_result(task)

class BackgroundProcessor:
    """Process non-critical tasks with unlimited time"""
    
    def __init__(self):
        self.worker_pool = asyncio.create_task
        self.task_queue = asyncio.Queue()
        self.max_concurrent_tasks = 3
        self.current_tasks = set()
    
    async def process(self, task: AITask) -> TaskResult:
        """Queue task for background processing"""
        await self.task_queue.put(task)
        
        # Start worker if slots available
        if len(self.current_tasks) < self.max_concurrent_tasks:
            worker_task = asyncio.create_task(self._worker())
            self.current_tasks.add(worker_task)
            worker_task.add_done_callback(self.current_tasks.discard)
        
        # Return immediate acknowledgment
        return TaskResult(status="queued", message="Task queued for processing")
    
    async def _worker(self) -> None:
        """Background worker for processing queued tasks"""
        while True:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._process_background_task(task)
            except asyncio.TimeoutError:
                break  # No tasks available, exit worker
            except Exception as e:
                logging.error(f"Background task failed: {e}")
```

#### 2. Preemptive Background Processing
**Predictive Background Processing**:

```python
class PredictiveBackgroundProcessor:
    """Preemptively process likely-needed computations"""
    
    def __init__(self):
        self.predictor = TaskPredictor()
        self.precompute_cache = PrecomputeCache()
        self.usage_patterns = UsagePatternTracker()
    
    async def start_predictive_processing(self, current_context: GameContext) -> None:
        """Start precomputing likely future needs"""
        predictions = self.predictor.predict_likely_tasks(current_context)
        
        for prediction in predictions:
            if prediction.probability > 0.7:  # High confidence predictions
                asyncio.create_task(
                    self._precompute_task(prediction.task, prediction.context)
                )
    
    async def _precompute_task(self, task: AITask, context: GameContext) -> None:
        """Precompute task result for future use"""
        try:
            result = await self._compute_full_result(task, context)
            self.precompute_cache.store(task, context, result)
            
            # Track success for improving predictions
            self.usage_patterns.record_precompute_success(task, context)
            
        except Exception as e:
            logging.warning(f"Precompute failed for {task}: {e}")
    
    async def get_precomputed_result(
        self,
        task: AITask,
        context: GameContext
    ) -> Optional[TaskResult]:
        """Get precomputed result if available"""
        return self.precompute_cache.get(task, context)

class TaskPredictor:
    """Predict likely future tasks based on current context"""
    
    def __init__(self):
        self.pattern_db = PatternDatabase()
        self.sequence_analyzer = SequenceAnalyzer()
    
    def predict_likely_tasks(self, context: GameContext) -> List[TaskPrediction]:
        """Predict tasks likely to be needed soon"""
        predictions = []
        
        # Pattern-based predictions
        similar_contexts = self.pattern_db.find_similar(context)
        for similar_context in similar_contexts:
            following_tasks = self.pattern_db.get_following_tasks(similar_context)
            for task in following_tasks:
                predictions.append(TaskPrediction(
                    task=task,
                    context=context,
                    probability=similar_context.similarity * task.frequency,
                    reasoning="Pattern-based prediction"
                ))
        
        # Sequence-based predictions
        recent_sequence = context.get_recent_task_sequence()
        sequence_predictions = self.sequence_analyzer.predict_next_tasks(recent_sequence)
        predictions.extend(sequence_predictions)
        
        # Sort by probability and return top candidates
        predictions.sort(key=lambda p: p.probability, reverse=True)
        return predictions[:5]  # Top 5 predictions
```

### Performance Monitoring Guidelines

#### 1. Real-Time Performance Metrics
**Critical Performance Monitoring**:

```python
class RealTimePerformanceMonitor:
    """Monitor performance with minimal overhead"""
    
    def __init__(self):
        self.metrics = {
            "frame_times": collections.deque(maxlen=3600),  # 1 minute of frames
            "cache_hit_rates": collections.deque(maxlen=300),  # 5 seconds
            "processing_violations": collections.deque(maxlen=100),
            "memory_usage": collections.deque(maxlen=60),  # 1 second
        }
        self.alert_thresholds = {
            "avg_frame_time": 15.0,  # ms
            "p95_frame_time": 16.0,  # ms
            "cache_hit_rate": 0.8,   # 80%
            "memory_usage": 0.8,     # 80% of available
        }
        self.performance_alerts = PerformanceAlerts()
    
    def record_frame_time(self, frame_time: float) -> None:
        """Record frame processing time with minimal overhead"""
        self.metrics["frame_times"].append(frame_time)
        
        # Check for immediate violations
        if frame_time > 16.7:
            self.performance_alerts.frame_budget_exceeded(frame_time)
    
    def record_cache_performance(self, hit_rate: float) -> None:
        """Record cache hit rate"""
        self.metrics["cache_hit_rates"].append(hit_rate)
        
        if hit_rate < self.alert_thresholds["cache_hit_rate"]:
            self.performance_alerts.cache_performance_degraded(hit_rate)
    
    def get_performance_summary(self) -> PerformanceSummary:
        """Get current performance summary"""
        frame_times = list(self.metrics["frame_times"])
        if not frame_times:
            return PerformanceSummary.empty()
        
        return PerformanceSummary(
            avg_frame_time=sum(frame_times) / len(frame_times),
            p95_frame_time=sorted(frame_times)[int(len(frame_times) * 0.95)],
            max_frame_time=max(frame_times),
            frames_over_budget=len([ft for ft in frame_times if ft > 16.7]),
            cache_hit_rate=self._calculate_recent_cache_hit_rate(),
            memory_usage=self._get_current_memory_usage(),
            timestamp=time.time()
        )
    
    def should_trigger_performance_alert(self) -> bool:
        """Check if performance alert should be triggered"""
        summary = self.get_performance_summary()
        
        # Check multiple conditions
        conditions = [
            summary.avg_frame_time > self.alert_thresholds["avg_frame_time"],
            summary.p95_frame_time > self.alert_thresholds["p95_frame_time"],
            summary.cache_hit_rate < self.alert_thresholds["cache_hit_rate"],
            summary.memory_usage > self.alert_thresholds["memory_usage"]
        ]
        
        return any(conditions)

class PerformanceAlerts:
    """Handle performance alerts and automated responses"""
    
    def __init__(self):
        self.alert_history = collections.deque(maxlen=100)
        self.automated_responses = AutomatedResponseManager()
    
    def frame_budget_exceeded(self, frame_time: float) -> None:
        """Handle frame budget violation"""
        alert = PerformanceAlert(
            type="frame_budget_exceeded",
            severity="high",
            value=frame_time,
            threshold=16.7,
            timestamp=time.time()
        )
        
        self.alert_history.append(alert)
        
        # Trigger automated response
        self.automated_responses.handle_frame_budget_violation(frame_time)
    
    def cache_performance_degraded(self, hit_rate: float) -> None:
        """Handle cache performance degradation"""
        alert = PerformanceAlert(
            type="cache_degradation",
            severity="medium",
            value=hit_rate,
            threshold=0.8,
            timestamp=time.time()
        )
        
        self.alert_history.append(alert)
        
        # Trigger cache optimization
        self.automated_responses.optimize_cache_performance()

class AutomatedResponseManager:
    """Automated responses to performance issues"""
    
    def __init__(self):
        self.response_strategies = {
            "frame_budget_violation": [
                "reduce_strategic_frequency",
                "simplify_pattern_matching",
                "disable_non_critical_features"
            ],
            "cache_degradation": [
                "increase_cache_size",
                "improve_cache_prediction",
                "preload_likely_patterns"
            ],
            "memory_pressure": [
                "clear_old_cache_entries",
                "reduce_background_processing",
                "trigger_garbage_collection"
            ]
        }
    
    def handle_frame_budget_violation(self, frame_time: float) -> None:
        """Automatically respond to frame budget violations"""
        if frame_time > 20.0:  # Severe violation
            # Immediate emergency response
            self._emergency_performance_mode()
        elif frame_time > 18.0:  # Moderate violation
            self._reduce_processing_load()
        else:
            # Minor violation, just log and monitor
            logging.warning(f"Frame time {frame_time:.2f}ms exceeds budget")
    
    def _emergency_performance_mode(self) -> None:
        """Enter emergency performance mode"""
        logging.critical("Entering emergency performance mode")
        
        # Disable all non-critical processing
        GlobalSettings.disable_background_processing = True
        GlobalSettings.strategic_frequency = 0.5  # Minimum
        GlobalSettings.cache_only_mode = True
        
        # Clear memory to free resources
        gc.collect()
```

### Performance Implementation Checklist

#### Architecture Phase
- [ ] Define performance budgets for all operations
- [ ] Design multi-frequency processing architecture  
- [ ] Plan hierarchical caching strategy
- [ ] Separate critical from non-critical paths

#### Implementation Phase
- [ ] Implement timing measurement for all operations
- [ ] Create adaptive frequency scaling
- [ ] Build multi-level cache system
- [ ] Add context-aware cache invalidation
- [ ] Implement predictive background processing

#### Monitoring Phase
- [ ] Set up real-time performance monitoring
- [ ] Configure automated performance alerts
- [ ] Implement performance degradation responses
- [ ] Track cache performance metrics

#### Optimization Phase
- [ ] Profile critical path operations
- [ ] Optimize cache hit rates
- [ ] Tune background processing priorities
- [ ] Validate performance under load

### Performance Anti-Patterns to Avoid

#### 1. Synchronous Everything
**Problem**: Blocking operations in critical path
**Solution**: Async/background processing for non-critical operations

#### 2. No Performance Budgets
**Problem**: Unclear performance requirements
**Solution**: Explicit timing budgets for every operation

#### 3. Uniform Processing Frequency
**Problem**: Processing everything at 60 FPS
**Solution**: Multi-frequency architecture based on priority

#### 4. Cache-Last Design
**Problem**: Adding caching as an afterthought
**Solution**: Cache-first architecture design

#### 5. No Performance Monitoring
**Problem**: Performance issues discovered too late
**Solution**: Real-time performance monitoring and alerting

This performance-first specification ensures AI systems maintain real-time performance while providing sophisticated capabilities through intelligent architectural design rather than brute-force optimization.