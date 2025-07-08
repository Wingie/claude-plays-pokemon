# AI Gaming System Specification
## Specialized Patterns for AI Game-Playing Systems

### Executive Summary

This specification defines architectural patterns and requirements specifically for AI systems that play video games in real-time. Based on lessons learned from the eevee_v1 complexity crisis and eevee_v2 architectural breakthrough, this document provides proven patterns for building AI gaming systems that are both sophisticated and maintainable.

### Game Integration Architecture Patterns

#### 1. Emulator Integration Pattern
**Principle**: Separate game control from AI logic through clean interfaces.

**Eevee_v1 Problem**: Tight coupling between AI and game control
- AI logic mixed with emulator-specific code
- Button mapping scattered throughout codebase
- Different emulators required different AI implementations

**Eevee_v2 Solution**: Clean abstraction layers
```python
from abc import ABC, abstractmethod

class GameControllerInterface(ABC):
    """Abstract interface for all game controllers"""
    
    @abstractmethod
    async def capture_frame(self) -> GameFrame:
        """Capture current game frame"""
        pass
    
    @abstractmethod
    async def send_input(self, button: str, duration: float = 0.1) -> bool:
        """Send button input to game"""
        pass
    
    @abstractmethod
    async def pause_game(self) -> bool:
        """Pause game for strategic thinking"""
        pass
    
    @abstractmethod
    async def resume_game(self) -> bool:
        """Resume game after strategic thinking"""
        pass
    
    @abstractmethod
    async def get_game_state(self) -> Dict[str, Any]:
        """Get detailed game state (RAM, save data, etc.)"""
        pass

class SkyEmuController(GameControllerInterface):
    """SkyEmu-specific implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.base_url = f"http://{host}:{port}"
        self.session = aiohttp.ClientSession()
        self.button_mapping = {
            "a": "A", "b": "B", "start": "Start", "select": "Select",
            "up": "Up", "down": "Down", "left": "Left", "right": "Right",
            "l": "L", "r": "R"
        }
    
    async def capture_frame(self) -> GameFrame:
        """Capture frame using SkyEmu HTTP API"""
        async with self.session.get(f"{self.base_url}/screenshot") as resp:
            image_data = await resp.read()
            return GameFrame(image_data, self._extract_metadata(resp))
    
    async def send_input(self, button: str, duration: float = 0.1) -> bool:
        """Send button input via HTTP"""
        mapped_button = self.button_mapping.get(button, button)
        payload = {"button": mapped_button, "duration": duration}
        
        async with self.session.post(f"{self.base_url}/input", json=payload) as resp:
            return resp.status == 200
    
    async def pause_game(self) -> bool:
        """Pause emulator for strategic thinking"""
        async with self.session.post(f"{self.base_url}/pause") as resp:
            return resp.status == 200
    
    async def resume_game(self) -> bool:
        """Resume emulator after thinking"""
        async with self.session.post(f"{self.base_url}/resume") as resp:
            return resp.status == 200

class PyBoyController(GameControllerInterface):
    """PyBoy-specific implementation for Game Boy games"""
    
    def __init__(self, rom_path: str):
        import pyboy
        self.pyboy = pyboy.PyBoy(rom_path)
        self.button_mapping = {
            "a": pyboy.WindowEvent.PRESS_BUTTON_A,
            "b": pyboy.WindowEvent.PRESS_BUTTON_B,
            "start": pyboy.WindowEvent.PRESS_BUTTON_START,
            "select": pyboy.WindowEvent.PRESS_BUTTON_SELECT,
            "up": pyboy.WindowEvent.PRESS_ARROW_UP,
            "down": pyboy.WindowEvent.PRESS_ARROW_DOWN,
            "left": pyboy.WindowEvent.PRESS_ARROW_LEFT,
            "right": pyboy.WindowEvent.PRESS_ARROW_RIGHT
        }
    
    async def capture_frame(self) -> GameFrame:
        """Capture frame from PyBoy"""
        screen_array = self.pyboy.screen.ndarray
        return GameFrame(screen_array, {"emulator": "pyboy"})
    
    async def send_input(self, button: str, duration: float = 0.1) -> bool:
        """Send input to PyBoy"""
        if button not in self.button_mapping:
            return False
        
        # Press button
        self.pyboy.button_press(self.button_mapping[button])
        
        # Hold for duration
        frames_to_hold = int(duration * 60)  # 60 FPS
        for _ in range(frames_to_hold):
            self.pyboy.tick()
        
        # Release button
        self.pyboy.button_release(self.button_mapping[button])
        return True

class GameControllerFactory:
    """Factory for creating appropriate game controllers"""
    
    @staticmethod
    def create_controller(game_config: GameConfig) -> GameControllerInterface:
        """Create controller based on game configuration"""
        if game_config.emulator_type == "skyemu":
            return SkyEmuController(
                host=game_config.host,
                port=game_config.port
            )
        elif game_config.emulator_type == "pyboy":
            return PyBoyController(game_config.rom_path)
        elif game_config.emulator_type == "mgba":
            return MGBAController(game_config.rom_path)
        else:
            raise ValueError(f"Unsupported emulator: {game_config.emulator_type}")
```

#### 2. Game State Abstraction Pattern
**Principle**: Abstract game-specific state into common interfaces.

**Universal Game State Interface**:
```python
class GameState:
    """Universal game state representation"""
    
    def __init__(self):
        self.raw_frame: Optional[np.ndarray] = None
        self.processed_frame: Optional[np.ndarray] = None
        self.player_position: Optional[Position] = None
        self.health: Optional[HealthInfo] = None
        self.inventory: Optional[Inventory] = None
        self.current_area: Optional[str] = None
        self.menu_state: Optional[MenuState] = None
        self.battle_state: Optional[BattleState] = None
        self.objectives: List[Objective] = []
        self.metadata: Dict[str, Any] = {}
        self.timestamp: float = time.time()
    
    @classmethod
    def from_raw_data(cls, controller: GameControllerInterface) -> 'GameState':
        """Create GameState from raw controller data"""
        state = cls()
        
        # Get raw frame
        frame = await controller.capture_frame()
        state.raw_frame = frame.image_data
        
        # Get detailed game state if available
        try:
            raw_state = await controller.get_game_state()
            state.metadata = raw_state
            
            # Extract common elements
            state.player_position = cls._extract_position(raw_state)
            state.health = cls._extract_health(raw_state)
            state.inventory = cls._extract_inventory(raw_state)
            
        except NotImplementedError:
            # Fallback to visual analysis only
            pass
        
        return state
    
    @staticmethod
    def _extract_position(raw_state: Dict[str, Any]) -> Optional[Position]:
        """Extract player position from raw state"""
        if "player_x" in raw_state and "player_y" in raw_state:
            return Position(raw_state["player_x"], raw_state["player_y"])
        return None
    
    @staticmethod
    def _extract_health(raw_state: Dict[str, Any]) -> Optional[HealthInfo]:
        """Extract health information from raw state"""
        if "current_hp" in raw_state and "max_hp" in raw_state:
            return HealthInfo(
                current=raw_state["current_hp"],
                maximum=raw_state["max_hp"],
                percentage=raw_state["current_hp"] / raw_state["max_hp"]
            )
        return None

class GameStateProcessor:
    """Process raw game state into AI-friendly format"""
    
    def __init__(self, game_type: str):
        self.game_type = game_type
        self.processors = {
            "pokemon": PokemonStateProcessor(),
            "mario": MarioStateProcessor(),
            "zelda": ZeldaStateProcessor()
        }
    
    async def process_state(self, raw_state: GameState) -> ProcessedGameState:
        """Process raw state into structured format"""
        processor = self.processors.get(self.game_type)
        if processor:
            return await processor.process(raw_state)
        else:
            return await self._generic_process(raw_state)
    
    async def _generic_process(self, raw_state: GameState) -> ProcessedGameState:
        """Generic processing for unknown game types"""
        return ProcessedGameState(
            visual_features=await self._extract_visual_features(raw_state.raw_frame),
            spatial_info=await self._extract_spatial_info(raw_state.raw_frame),
            interactive_elements=await self._detect_interactive_elements(raw_state.raw_frame),
            text_elements=await self._extract_text(raw_state.raw_frame)
        )
```

### Visual Analysis Preprocessing

#### 1. Game-Specific Visual Processing
**Principle**: Preprocess visuals to make them understandable to vision models.

**Tile-Based Game Processing (for GBA/GB games)**:
```python
class TileBasedGameProcessor:
    """Process tile-based games (Pokemon, Fire Emblem, etc.)"""
    
    def __init__(self, tile_size: int = 8):
        self.tile_size = tile_size
        self.tile_classifier = TileClassifier()
        self.overlay_generator = OverlayGenerator()
    
    async def process_frame_for_ai(self, frame: np.ndarray) -> ProcessedFrame:
        """Process game frame for AI understanding"""
        # 1. Detect tile grid
        tile_grid = self._detect_tile_grid(frame)
        
        # 2. Classify each tile
        classified_tiles = await self._classify_tiles(tile_grid)
        
        # 3. Generate semantic overlay
        semantic_overlay = self._generate_semantic_overlay(frame, classified_tiles)
        
        # 4. Add spatial annotations
        annotated_frame = self._add_spatial_annotations(semantic_overlay, classified_tiles)
        
        # 5. Generate text description
        spatial_description = self._generate_spatial_description(classified_tiles)
        
        return ProcessedFrame(
            original_frame=frame,
            annotated_frame=annotated_frame,
            tile_grid=classified_tiles,
            spatial_description=spatial_description,
            interactive_elements=self._find_interactive_elements(classified_tiles)
        )
    
    def _detect_tile_grid(self, frame: np.ndarray) -> TileGrid:
        """Detect 8x8 tile structure in frame"""
        height, width = frame.shape[:2]
        
        tile_grid = TileGrid(
            width=width // self.tile_size,
            height=height // self.tile_size,
            tile_size=self.tile_size
        )
        
        for y in range(0, height, self.tile_size):
            for x in range(0, width, self.tile_size):
                tile_data = frame[y:y+self.tile_size, x:x+self.tile_size]
                tile_grid.set_tile(x // self.tile_size, y // self.tile_size, tile_data)
        
        return tile_grid
    
    async def _classify_tiles(self, tile_grid: TileGrid) -> ClassifiedTileGrid:
        """Classify each tile type"""
        classified_grid = ClassifiedTileGrid(tile_grid.width, tile_grid.height)
        
        for x in range(tile_grid.width):
            for y in range(tile_grid.height):
                tile_data = tile_grid.get_tile(x, y)
                tile_type = await self.tile_classifier.classify(tile_data)
                classified_grid.set_tile(x, y, tile_type)
        
        return classified_grid
    
    def _generate_semantic_overlay(
        self,
        frame: np.ndarray,
        classified_tiles: ClassifiedTileGrid
    ) -> np.ndarray:
        """Generate visual overlay with semantic information"""
        overlay = frame.copy()
        
        for x in range(classified_tiles.width):
            for y in range(classified_tiles.height):
                tile_type = classified_tiles.get_tile(x, y)
                color = self._get_semantic_color(tile_type)
                
                # Draw colored border around tile
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                cv2.rectangle(
                    overlay,
                    (pixel_x, pixel_y),
                    (pixel_x + self.tile_size, pixel_y + self.tile_size),
                    color,
                    1
                )
        
        return overlay
    
    def _get_semantic_color(self, tile_type: TileType) -> Tuple[int, int, int]:
        """Get color for semantic overlay"""
        color_mapping = {
            TileType.WALKABLE: (0, 255, 0),      # Green
            TileType.WALL: (255, 0, 0),          # Red
            TileType.WATER: (255, 255, 0),       # Cyan
            TileType.DOOR: (0, 255, 255),        # Yellow
            TileType.NPC: (255, 0, 255),         # Magenta
            TileType.ITEM: (0, 128, 255),        # Orange
            TileType.PLAYER: (255, 255, 255),    # White
            TileType.UNKNOWN: (128, 128, 128)    # Gray
        }
        return color_mapping.get(tile_type, (128, 128, 128))

class TileClassifier:
    """Classify tile types using computer vision"""
    
    def __init__(self):
        self.color_ranges = self._define_color_ranges()
        self.pattern_matcher = PatternMatcher()
        self.confidence_threshold = 0.7
    
    async def classify(self, tile_data: np.ndarray) -> TileType:
        """Classify a single tile"""
        # 1. Color-based classification
        color_classification = self._classify_by_color(tile_data)
        
        # 2. Pattern-based classification
        pattern_classification = await self._classify_by_pattern(tile_data)
        
        # 3. Combine classifications
        final_classification = self._combine_classifications(
            color_classification,
            pattern_classification
        )
        
        return final_classification
    
    def _classify_by_color(self, tile_data: np.ndarray) -> ClassificationResult:
        """Classify tile based on dominant colors"""
        # Convert to HSV for better color analysis
        hsv_tile = cv2.cvtColor(tile_data, cv2.COLOR_RGB2HSV)
        
        for tile_type, color_range in self.color_ranges.items():
            mask = cv2.inRange(hsv_tile, color_range.lower, color_range.upper)
            coverage = np.sum(mask > 0) / mask.size
            
            if coverage > 0.6:  # 60% coverage threshold
                return ClassificationResult(tile_type, coverage)
        
        return ClassificationResult(TileType.UNKNOWN, 0.0)
```

#### 2. Multi-Modal Frame Processing
**Principle**: Combine visual and textual information for better AI understanding.

**Multi-Modal Frame Processor**:
```python
class MultiModalFrameProcessor:
    """Process frames using both visual and textual analysis"""
    
    def __init__(self):
        self.visual_processor = VisualFrameProcessor()
        self.text_extractor = GameTextExtractor()
        self.spatial_analyzer = SpatialAnalyzer()
        self.context_builder = ContextBuilder()
    
    async def process_frame(self, frame: np.ndarray, game_state: GameState) -> MultiModalFrame:
        """Process frame with multiple modalities"""
        # Process visual information
        visual_analysis = await self.visual_processor.analyze(frame)
        
        # Extract text from frame
        text_elements = await self.text_extractor.extract_text(frame)
        
        # Analyze spatial relationships
        spatial_analysis = await self.spatial_analyzer.analyze(visual_analysis, text_elements)
        
        # Build context description
        context_description = await self.context_builder.build_description(
            visual_analysis,
            text_elements,
            spatial_analysis,
            game_state
        )
        
        return MultiModalFrame(
            original_frame=frame,
            visual_analysis=visual_analysis,
            text_elements=text_elements,
            spatial_analysis=spatial_analysis,
            context_description=context_description,
            ai_prompt=self._generate_ai_prompt(context_description)
        )
    
    def _generate_ai_prompt(self, context: ContextDescription) -> str:
        """Generate AI prompt from multi-modal analysis"""
        prompt_parts = [
            f"Current Location: {context.current_area}",
            f"Player Status: {context.player_status}",
            f"Visible Elements: {', '.join(context.visible_elements)}",
            f"Interactive Objects: {', '.join(context.interactive_objects)}",
            f"Current Objective: {context.current_objective}",
            f"Available Actions: {', '.join(context.available_actions)}"
        ]
        
        if context.text_content:
            prompt_parts.append(f"Screen Text: {context.text_content}")
        
        if context.spatial_layout:
            prompt_parts.append(f"Spatial Layout: {context.spatial_layout}")
        
        return "\n".join(prompt_parts)

class GameTextExtractor:
    """Extract and interpret text from game frames"""
    
    def __init__(self):
        self.ocr_engine = self._initialize_ocr()
        self.text_filters = TextFilters()
        self.game_text_patterns = GameTextPatterns()
    
    async def extract_text(self, frame: np.ndarray) -> List[TextElement]:
        """Extract text elements from frame"""
        # Preprocess frame for better OCR
        processed_frame = self._preprocess_for_ocr(frame)
        
        # Run OCR
        raw_text_results = await self._run_ocr(processed_frame)
        
        # Filter and classify text
        filtered_text = self._filter_game_text(raw_text_results)
        
        # Classify text types (menu, dialogue, status, etc.)
        classified_text = self._classify_text_types(filtered_text)
        
        return classified_text
    
    def _preprocess_for_ocr(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for better OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Enhance contrast
        enhanced = cv2.equalizeHist(gray)
        
        # Upscale for better OCR
        upscaled = cv2.resize(enhanced, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        denoised = cv2.medianBlur(upscaled, 3)
        
        return denoised
    
    def _classify_text_types(self, text_elements: List[RawTextElement]) -> List[TextElement]:
        """Classify text elements by type"""
        classified = []
        
        for element in text_elements:
            text_type = self._determine_text_type(element)
            importance = self._calculate_importance(element, text_type)
            
            classified.append(TextElement(
                text=element.text,
                position=element.position,
                confidence=element.confidence,
                text_type=text_type,
                importance=importance
            ))
        
        return classified
    
    def _determine_text_type(self, element: RawTextElement) -> TextType:
        """Determine the type of text element"""
        text = element.text.lower()
        position = element.position
        
        # Menu text (usually at top or in organized lists)
        if self._is_menu_position(position) and any(
            keyword in text for keyword in ["pokemon", "items", "save", "options"]
        ):
            return TextType.MENU
        
        # Dialogue text (usually in bottom area)
        elif self._is_dialogue_position(position) and len(text) > 10:
            return TextType.DIALOGUE
        
        # Status text (numbers, HP, level, etc.)
        elif any(keyword in text for keyword in ["hp", "lv", "exp", "%"]):
            return TextType.STATUS
        
        # Location text
        elif self._is_location_text(text):
            return TextType.LOCATION
        
        else:
            return TextType.UNKNOWN
```

### Strategic vs Tactical Decision Separation

#### 1. Decision Layer Architecture
**Principle**: Separate high-level strategy from low-level tactics.

**Strategic Decision Layer**:
```python
class StrategicDecisionLayer:
    """High-level strategic planning (pause-based, unlimited time)"""
    
    def __init__(self):
        self.vision_model = VisionLanguageModel()
        self.goal_manager = GoalManager()
        self.world_model = WorldModel()
        self.strategy_cache = StrategyCache()
    
    async def create_strategy(self, game_context: GameContext) -> Strategy:
        """Create high-level strategy (can pause game)"""
        await game_context.controller.pause_game()
        
        try:
            # Deep visual analysis (200ms)
            visual_analysis = await self.vision_model.analyze_deeply(
                game_context.processed_frame
            )
            
            # Update world model (100ms)
            await self.world_model.update(visual_analysis, game_context.game_state)
            
            # Strategic planning (200ms)
            current_goals = self.goal_manager.get_active_goals()
            strategy = await self._plan_strategy(visual_analysis, current_goals)
            
            # Cache strategy for tactical layer
            self.strategy_cache.store(game_context, strategy)
            
            return strategy
            
        finally:
            await game_context.controller.resume_game()
    
    async def _plan_strategy(
        self,
        visual_analysis: VisualAnalysis,
        goals: List[Goal]
    ) -> Strategy:
        """Plan high-level strategy"""
        prompt = f"""
        Analyze the current Pokemon game situation and create a strategic plan.
        
        Visual Analysis: {visual_analysis.description}
        Current Area: {visual_analysis.current_area}
        Visible NPCs: {visual_analysis.npcs}
        Interactive Objects: {visual_analysis.interactive_objects}
        
        Active Goals:
        {self._format_goals(goals)}
        
        Create a strategic plan with:
        1. Primary objective for next 30-60 seconds
        2. Key waypoints or sub-goals
        3. Success criteria
        4. Failure conditions and backup plans
        5. Resource management priorities
        
        Format as structured strategy that tactical layer can execute.
        """
        
        response = await self.vision_model.generate_strategy(prompt, visual_analysis.frame)
        return Strategy.from_llm_response(response)
    
    def _format_goals(self, goals: List[Goal]) -> str:
        """Format goals for prompt"""
        formatted = []
        for goal in sorted(goals, key=lambda g: g.priority, reverse=True):
            formatted.append(f"- {goal.description} (Priority: {goal.priority})")
        return "\n".join(formatted)

class TacticalDecisionLayer:
    """Low-level tactical execution (≤5ms, real-time)"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.action_cache = ActionCache()
        self.tactical_rules = TacticalRules()
        self.safety_checker = SafetyChecker()
    
    async def execute_tactics(self, game_context: GameContext) -> Action:
        """Execute tactical decision (must be ≤5ms)"""
        start_time = time.perf_counter()
        
        try:
            # Get current strategy
            current_strategy = self.strategy_cache.get_current(game_context)
            
            if not current_strategy:
                return self._get_safe_fallback_action(game_context)
            
            # Match current situation to tactical pattern
            tactical_pattern = self.pattern_matcher.match_tactical_situation(
                game_context.processed_frame,
                current_strategy
            )
            
            # Get cached tactical action
            tactical_action = self.action_cache.get_tactical_action(
                tactical_pattern,
                current_strategy.current_phase
            )
            
            if tactical_action:
                # Validate action safety
                if self.safety_checker.is_safe(tactical_action, game_context):
                    return tactical_action
            
            # Fallback to rule-based tactics
            rule_based_action = self.tactical_rules.get_action(
                tactical_pattern,
                current_strategy
            )
            
            return rule_based_action
            
        finally:
            # Ensure timing constraint
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 5.0:
                logging.warning(f"Tactical decision took {elapsed:.2f}ms (budget: 5ms)")
    
    def _get_safe_fallback_action(self, game_context: GameContext) -> Action:
        """Get safe action when no strategy available"""
        # Ultra-fast fallback (≤1ms)
        if game_context.game_state.health and game_context.game_state.health.percentage < 0.2:
            return Action.SEEK_HEALING
        elif self._detect_stuck_pattern(game_context):
            return Action.RANDOM_EXPLORATION
        else:
            return Action.CONTINUE_EXPLORATION

class TacticalRules:
    """Rule-based tactical decisions for common situations"""
    
    def __init__(self):
        self.rules = self._build_tactical_rules()
    
    def _build_tactical_rules(self) -> List[TacticalRule]:
        """Build rule set for tactical decisions"""
        return [
            # Combat rules
            TacticalRule(
                pattern="in_battle_player_turn",
                condition=lambda ctx: ctx.battle_state and ctx.battle_state.player_turn,
                action=self._choose_battle_action,
                priority=10
            ),
            
            # Navigation rules
            TacticalRule(
                pattern="blocked_movement",
                condition=lambda ctx: self._is_movement_blocked(ctx),
                action=self._navigate_around_obstacle,
                priority=8
            ),
            
            # Interaction rules
            TacticalRule(
                pattern="npc_nearby",
                condition=lambda ctx: self._npc_in_interaction_range(ctx),
                action=Action.INTERACT,
                priority=7
            ),
            
            # Safety rules
            TacticalRule(
                pattern="low_health",
                condition=lambda ctx: ctx.game_state.health.percentage < 0.3,
                action=Action.USE_HEALING_ITEM,
                priority=9
            )
        ]
    
    def get_action(self, pattern: TacticalPattern, strategy: Strategy) -> Action:
        """Get rule-based action for pattern"""
        applicable_rules = [
            rule for rule in self.rules
            if rule.matches(pattern) and rule.condition(pattern.context)
        ]
        
        if applicable_rules:
            # Use highest priority rule
            best_rule = max(applicable_rules, key=lambda r: r.priority)
            return best_rule.get_action(pattern.context)
        
        # Default exploration action
        return self._get_exploration_action(strategy)
```

#### 2. Goal-Oriented Behavior System
**Principle**: Drive behavior through explicit goal hierarchies.

**Hierarchical Goal System**:
```python
class GoalManager:
    """Manage hierarchical goal structure"""
    
    def __init__(self):
        self.goal_hierarchy = GoalHierarchy()
        self.goal_tracker = GoalTracker()
        self.goal_generator = DynamicGoalGenerator()
    
    def get_active_goals(self) -> List[Goal]:
        """Get currently active goals in priority order"""
        return self.goal_hierarchy.get_active_goals()
    
    async def update_goals(self, game_context: GameContext) -> None:
        """Update goal hierarchy based on current situation"""
        # Check for completed goals
        completed_goals = self.goal_tracker.check_completed_goals(game_context)
        for goal in completed_goals:
            await self._complete_goal(goal, game_context)
        
        # Check for failed goals
        failed_goals = self.goal_tracker.check_failed_goals(game_context)
        for goal in failed_goals:
            await self._handle_failed_goal(goal, game_context)
        
        # Generate new goals if needed
        new_goals = await self.goal_generator.generate_goals(game_context)
        for goal in new_goals:
            self.goal_hierarchy.add_goal(goal)
    
    async def _complete_goal(self, goal: Goal, context: GameContext) -> None:
        """Handle goal completion"""
        # Mark goal as completed
        self.goal_hierarchy.complete_goal(goal)
        
        # Generate follow-up goals
        follow_up_goals = await self._generate_follow_up_goals(goal, context)
        for follow_up in follow_up_goals:
            self.goal_hierarchy.add_goal(follow_up)
        
        # Update strategy cache
        self.strategy_cache.invalidate_goals_pattern()

class GoalHierarchy:
    """Hierarchical goal structure with priorities"""
    
    def __init__(self):
        self.goals = {
            "survival": [],      # Priority 10 (highest)
            "main_quest": [],    # Priority 8
            "side_quest": [],    # Priority 6
            "exploration": [],   # Priority 4
            "collection": [],    # Priority 3
            "optimization": []   # Priority 2 (lowest)
        }
        self.goal_dependencies = GoalDependencyGraph()
    
    def add_goal(self, goal: Goal) -> None:
        """Add goal to appropriate category"""
        category = self._categorize_goal(goal)
        self.goals[category].append(goal)
        
        # Sort by priority within category
        self.goals[category].sort(key=lambda g: g.priority, reverse=True)
    
    def get_active_goals(self) -> List[Goal]:
        """Get active goals in priority order"""
        active_goals = []
        
        for category in ["survival", "main_quest", "side_quest", "exploration", "collection", "optimization"]:
            for goal in self.goals[category]:
                if goal.status == GoalStatus.ACTIVE and self._dependencies_met(goal):
                    active_goals.append(goal)
        
        return active_goals
    
    def _categorize_goal(self, goal: Goal) -> str:
        """Categorize goal based on type and urgency"""
        if goal.type == GoalType.SURVIVAL:
            return "survival"
        elif goal.type == GoalType.MAIN_STORY:
            return "main_quest"
        elif goal.type == GoalType.SIDE_QUEST:
            return "side_quest"
        elif goal.type == GoalType.EXPLORATION:
            return "exploration"
        elif goal.type == GoalType.ITEM_COLLECTION:
            return "collection"
        else:
            return "optimization"
    
    def _dependencies_met(self, goal: Goal) -> bool:
        """Check if goal dependencies are satisfied"""
        dependencies = self.goal_dependencies.get_dependencies(goal)
        return all(dep.status == GoalStatus.COMPLETED for dep in dependencies)

class DynamicGoalGenerator:
    """Generate goals dynamically based on game state"""
    
    def __init__(self):
        self.goal_templates = GoalTemplates()
        self.situation_analyzer = SituationAnalyzer()
        self.goal_history = GoalHistory()
    
    async def generate_goals(self, game_context: GameContext) -> List[Goal]:
        """Generate appropriate goals for current situation"""
        new_goals = []
        
        # Analyze current situation
        situation = await self.situation_analyzer.analyze(game_context)
        
        # Generate survival goals if needed
        if situation.health_critical:
            healing_goal = self.goal_templates.create_healing_goal(situation)
            new_goals.append(healing_goal)
        
        # Generate exploration goals for new areas
        if situation.new_area_detected:
            exploration_goal = self.goal_templates.create_exploration_goal(situation.current_area)
            new_goals.append(exploration_goal)
        
        # Generate interaction goals for NPCs
        if situation.uninteracted_npcs:
            for npc in situation.uninteracted_npcs:
                if not self.goal_history.has_interacted_with(npc):
                    interaction_goal = self.goal_templates.create_interaction_goal(npc)
                    new_goals.append(interaction_goal)
        
        # Generate collection goals for visible items
        if situation.visible_items:
            for item in situation.visible_items:
                if self._should_collect_item(item, game_context):
                    collection_goal = self.goal_templates.create_collection_goal(item)
                    new_goals.append(collection_goal)
        
        return new_goals
    
    def _should_collect_item(self, item: Item, context: GameContext) -> bool:
        """Determine if item should be collected"""
        # Check if inventory has space
        if context.game_state.inventory and context.game_state.inventory.is_full():
            return item.priority > 7  # Only collect high-priority items
        
        # Check if item is useful
        if item.type == ItemType.HEALING and context.game_state.health.percentage < 0.8:
            return True
        
        if item.type == ItemType.KEY_ITEM:
            return True
        
        # Check if we already have enough of this item
        current_count = context.game_state.inventory.get_count(item.name)
        if current_count >= item.max_useful_count:
            return False
        
        return True
```

### Memory Persistence Patterns

#### 1. Spatial Memory System
**Principle**: Maintain persistent spatial knowledge across sessions.

**Spatial Memory Implementation**:
```python
class SpatialMemorySystem:
    """Persistent spatial memory for game worlds"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.spatial_graph = SpatialGraph()
        self.location_tracker = LocationTracker()
        self.pathfinding_cache = PathfindingCache()
        self.exploration_tracker = ExplorationTracker()
    
    async def update_location(self, position: Position, area: str, context: GameContext) -> None:
        """Update current location information"""
        location_node = LocationNode(
            position=position,
            area=area,
            timestamp=time.time(),
            visual_hash=self._hash_visual_context(context.processed_frame),
            accessible_directions=await self._detect_accessible_directions(context),
            interactive_objects=await self._detect_interactive_objects(context),
            landmarks=await self._detect_landmarks(context)
        )
        
        # Add or update location in spatial graph
        self.spatial_graph.add_location(location_node)
        
        # Update connections to nearby locations
        nearby_locations = self.spatial_graph.get_nearby_locations(position, radius=50)
        for nearby in nearby_locations:
            if self._can_connect_locations(location_node, nearby):
                connection = self._create_connection(location_node, nearby)
                self.spatial_graph.add_connection(connection)
        
        # Update exploration progress
        self.exploration_tracker.mark_explored(position, area)
    
    async def find_path_to_objective(self, current_pos: Position, objective: Objective) -> Optional[Path]:
        """Find path to objective using spatial memory"""
        # Check cache first
        cache_key = f"{current_pos}_{objective.location}"
        cached_path = self.pathfinding_cache.get(cache_key)
        if cached_path and cached_path.is_valid():
            return cached_path
        
        # Find path using spatial graph
        if objective.location_known:
            target_position = objective.location
            path = self.spatial_graph.find_path(current_pos, target_position)
        else:
            # Find path to unexplored areas near objective
            candidate_areas = self._find_candidate_exploration_areas(objective)
            path = self._find_best_exploration_path(current_pos, candidate_areas)
        
        # Cache the path
        if path:
            self.pathfinding_cache.store(cache_key, path)
        
        return path
    
    def _detect_accessible_directions(self, context: GameContext) -> List[Direction]:
        """Detect which directions are accessible from current position"""
        accessible = []
        
        # Analyze processed frame for walkable areas
        tile_grid = context.processed_frame.tile_grid
        player_tile = self._find_player_tile(tile_grid)
        
        if player_tile:
            # Check each direction
            for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                adjacent_pos = player_tile.position.move(direction)
                adjacent_tile = tile_grid.get_tile(adjacent_pos.x, adjacent_pos.y)
                
                if adjacent_tile and adjacent_tile.type in [TileType.WALKABLE, TileType.DOOR]:
                    accessible.append(direction)
        
        return accessible
    
    def _detect_interactive_objects(self, context: GameContext) -> List[InteractiveObject]:
        """Detect interactive objects near player"""
        interactive_objects = []
        
        # Analyze processed frame for interactive elements
        for element in context.processed_frame.interactive_elements:
            if element.distance_from_player < 20:  # Within interaction range
                interactive_obj = InteractiveObject(
                    type=element.type,
                    position=element.position,
                    interaction_type=element.interaction_type,
                    requirements=element.requirements
                )
                interactive_objects.append(interactive_obj)
        
        return interactive_objects

class SpatialGraph:
    """Graph representation of game world spatial relationships"""
    
    def __init__(self):
        self.locations = {}  # position -> LocationNode
        self.connections = {}  # (pos1, pos2) -> Connection
        self.areas = {}  # area_name -> AreaInfo
    
    def add_location(self, location_node: LocationNode) -> None:
        """Add or update location in graph"""
        pos_key = self._position_key(location_node.position)
        
        if pos_key in self.locations:
            # Update existing location
            existing = self.locations[pos_key]
            existing.merge_information(location_node)
        else:
            # Add new location
            self.locations[pos_key] = location_node
        
        # Update area information
        self._update_area_info(location_node)
    
    def find_path(self, start: Position, goal: Position) -> Optional[Path]:
        """Find path using A* algorithm on spatial graph"""
        start_key = self._position_key(start)
        goal_key = self._position_key(goal)
        
        if start_key not in self.locations or goal_key not in self.locations:
            return None
        
        # A* pathfinding
        open_set = [(0, start_key)]
        came_from = {}
        g_score = {start_key: 0}
        f_score = {start_key: self._heuristic(start, goal)}
        
        while open_set:
            current_f, current_key = heapq.heappop(open_set)
            current_pos = self.locations[current_key].position
            
            if current_key == goal_key:
                # Reconstruct path
                path_positions = []
                while current_key in came_from:
                    path_positions.append(self.locations[current_key].position)
                    current_key = came_from[current_key]
                path_positions.append(start)
                path_positions.reverse()
                
                return Path(path_positions, self._calculate_path_cost(path_positions))
            
            # Check neighbors
            for neighbor_key in self._get_connected_locations(current_key):
                neighbor_pos = self.locations[neighbor_key].position
                tentative_g = g_score[current_key] + self._connection_cost(current_pos, neighbor_pos)
                
                if neighbor_key not in g_score or tentative_g < g_score[neighbor_key]:
                    came_from[neighbor_key] = current_key
                    g_score[neighbor_key] = tentative_g
                    f_score[neighbor_key] = tentative_g + self._heuristic(neighbor_pos, goal)
                    heapq.heappush(open_set, (f_score[neighbor_key], neighbor_key))
        
        return None  # No path found
    
    def _heuristic(self, pos1: Position, pos2: Position) -> float:
        """A* heuristic function (Manhattan distance)"""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)
    
    def _connection_cost(self, pos1: Position, pos2: Position) -> float:
        """Cost of moving between two connected positions"""
        connection_key = self._connection_key(pos1, pos2)
        if connection_key in self.connections:
            return self.connections[connection_key].cost
        return float('inf')  # Not connected
```

### Testing Strategies for AI Gaming

#### 1. Deterministic Test Environment
**Principle**: Test AI behavior in controlled, repeatable environments.

**Test Environment Implementation**:
```python
class DeterministicGameEnvironment:
    """Controlled environment for testing AI behavior"""
    
    def __init__(self, test_scenario: str):
        self.test_scenario = test_scenario
        self.scenario_loader = ScenarioLoader()
        self.mock_controller = MockGameController()
        self.expected_behaviors = {}
        self.behavior_validator = BehaviorValidator()
    
    async def setup_scenario(self, scenario_name: str) -> None:
        """Set up deterministic test scenario"""
        scenario = await self.scenario_loader.load_scenario(scenario_name)
        
        # Configure mock controller with scenario data
        await self.mock_controller.configure(scenario)
        
        # Load expected behaviors
        self.expected_behaviors = scenario.expected_behaviors
        
        # Reset AI state
        await self._reset_ai_state()
    
    async def run_test_sequence(self, ai_agent: AIAgent, steps: int = 100) -> TestResult:
        """Run AI through test sequence and validate behavior"""
        test_result = TestResult(scenario=self.test_scenario)
        
        for step in range(steps):
            # Get current game state
            game_state = await self.mock_controller.get_game_state()
            
            # AI makes decision
            start_time = time.perf_counter()
            decision = await ai_agent.make_decision(game_state)
            decision_time = (time.perf_counter() - start_time) * 1000
            
            # Execute decision in mock environment
            result = await self.mock_controller.execute_action(decision.action)
            
            # Validate behavior
            behavior_check = await self.behavior_validator.validate_step(
                step, game_state, decision, result, self.expected_behaviors
            )
            
            test_result.add_step_result(StepResult(
                step=step,
                decision=decision,
                decision_time=decision_time,
                result=result,
                behavior_check=behavior_check
            ))
            
            # Check for test completion conditions
            if self._test_completed(result, step):
                break
        
        return test_result
    
    def _test_completed(self, result: ActionResult, step: int) -> bool:
        """Check if test scenario is completed"""
        return (
            result.scenario_completed or
            result.failure_condition_met or
            step >= 1000  # Maximum steps
        )

class MockGameController(GameControllerInterface):
    """Mock controller for deterministic testing"""
    
    def __init__(self):
        self.scenario_state = {}
        self.action_log = []
        self.frame_sequence = []
        self.current_frame_index = 0
        self.state_transitions = {}
    
    async def configure(self, scenario: TestScenario) -> None:
        """Configure mock controller with scenario data"""
        self.scenario_state = scenario.initial_state.copy()
        self.frame_sequence = scenario.frame_sequence
        self.state_transitions = scenario.state_transitions
        self.current_frame_index = 0
    
    async def capture_frame(self) -> GameFrame:
        """Return predetermined frame from sequence"""
        if self.current_frame_index < len(self.frame_sequence):
            frame_data = self.frame_sequence[self.current_frame_index]
            return GameFrame(frame_data, {"mock": True})
        else:
            # Return last frame if sequence exhausted
            return GameFrame(self.frame_sequence[-1], {"mock": True})
    
    async def send_input(self, button: str, duration: float = 0.1) -> bool:
        """Process input and update mock state"""
        self.action_log.append(ActionLogEntry(
            button=button,
            duration=duration,
            timestamp=time.time(),
            state_before=self.scenario_state.copy()
        ))
        
        # Apply state transition if defined
        transition_key = f"{button}_from_{self._get_state_key()}"
        if transition_key in self.state_transitions:
            transition = self.state_transitions[transition_key]
            self._apply_state_transition(transition)
        
        # Advance frame sequence
        self.current_frame_index += 1
        
        return True
    
    def _apply_state_transition(self, transition: StateTransition) -> None:
        """Apply state transition based on action"""
        for key, value in transition.state_changes.items():
            self.scenario_state[key] = value
        
        # Apply any special effects
        for effect in transition.effects:
            effect.apply(self.scenario_state)

class BehaviorValidator:
    """Validate AI behavior against expected patterns"""
    
    def __init__(self):
        self.behavior_rules = BehaviorRules()
        self.performance_thresholds = PerformanceThresholds()
    
    async def validate_step(
        self,
        step: int,
        game_state: GameState,
        decision: Decision,
        result: ActionResult,
        expected_behaviors: Dict[str, Any]
    ) -> BehaviorValidation:
        """Validate single step behavior"""
        validation = BehaviorValidation()
        
        # Check decision appropriateness
        appropriateness = await self._validate_decision_appropriateness(
            game_state, decision, expected_behaviors
        )
        validation.decision_appropriateness = appropriateness
        
        # Check timing performance
        timing_ok = decision.processing_time <= self.performance_thresholds.max_decision_time
        validation.timing_performance = timing_ok
        
        # Check goal progress
        goal_progress = await self._validate_goal_progress(
            game_state, decision, result, expected_behaviors
        )
        validation.goal_progress = goal_progress
        
        # Check safety constraints
        safety_ok = await self._validate_safety_constraints(
            game_state, decision, result
        )
        validation.safety_constraints = safety_ok
        
        return validation
    
    async def _validate_decision_appropriateness(
        self,
        game_state: GameState,
        decision: Decision,
        expected_behaviors: Dict[str, Any]
    ) -> bool:
        """Validate that decision is appropriate for current situation"""
        situation = self._classify_situation(game_state)
        expected_action_types = expected_behaviors.get(situation, [])
        
        return decision.action.type in expected_action_types
    
    def _classify_situation(self, game_state: GameState) -> str:
        """Classify current game situation"""
        if game_state.battle_state and game_state.battle_state.in_battle:
            return "battle"
        elif game_state.health and game_state.health.percentage < 0.3:
            return "low_health"
        elif game_state.menu_state and game_state.menu_state.menu_open:
            return "menu_navigation"
        elif self._near_interactive_object(game_state):
            return "interaction_opportunity"
        else:
            return "exploration"
```

### Implementation Checklist

#### Game Integration
- [ ] Define abstract game controller interface
- [ ] Implement emulator-specific controllers
- [ ] Create universal game state representation
- [ ] Build game state factory for different game types

#### Visual Processing
- [ ] Implement tile-based game processor
- [ ] Create semantic overlay generation
- [ ] Build text extraction and classification
- [ ] Add spatial relationship analysis

#### Decision Architecture
- [ ] Separate strategic and tactical decision layers
- [ ] Implement pause-based strategic reasoning
- [ ] Create real-time tactical execution
- [ ] Build rule-based tactical fallbacks

#### Goal System
- [ ] Design hierarchical goal structure
- [ ] Implement dynamic goal generation
- [ ] Create goal dependency tracking
- [ ] Add goal completion detection

#### Memory System
- [ ] Build spatial memory graph
- [ ] Implement pathfinding with memory
- [ ] Create exploration tracking
- [ ] Add persistent knowledge storage

#### Testing Framework
- [ ] Create deterministic test environments
- [ ] Build behavior validation system
- [ ] Implement performance testing
- [ ] Add regression test suites

This specification provides the foundational patterns for building sophisticated AI gaming systems while avoiding the complexity traps that plagued eevee_v1.