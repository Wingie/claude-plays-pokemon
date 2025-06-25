"""
Simplified Task-Based Memory System with Neo4j
Function-centric approach with minimal overhead and clear task relationships
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

# Neo4j imports with graceful fallback
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

@dataclass
class TaskResult:
    """Result of a task execution"""
    task_name: str
    success: bool
    output: Any
    execution_time: float
    error: Optional[str] = None
    context: Optional[Dict] = None

@dataclass 
class TaskNode:
    """Simple task definition"""
    name: str
    func: Callable
    dependencies: List[str] = None
    priority: int = 1
    timeout: float = 30.0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class SimplifiedTaskMemory:
    """Lightweight Neo4j task memory without heavy dependencies"""
    
    def __init__(self, session_name: str = "default", neo4j_uri: str = None):
        self.session_name = session_name
        self.neo4j_uri = neo4j_uri or "bolt://localhost:7687"
        self.driver = None
        self.connected = False
        
        # In-memory fallback for when Neo4j unavailable
        self.memory_store = {
            'tasks': {},
            'results': [],
            'patterns': {},
            'success_rates': {}
        }
        
        # Initialize connection
        if NEO4J_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """Simple connection with graceful fallback"""
        try:
            # Try connection with no auth (common in dev/testing)
            self.driver = GraphDatabase.driver(self.neo4j_uri, auth=None)
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1").single()
                self.connected = True
                self._setup_schema()
                
        except Exception as e:
            # Graceful fallback for testing
            print(f"⚠️  Neo4j not available: {e}")
            print("📝 Using in-memory fallback (normal for testing)")
            self.connected = False
            self.driver = None
    
    def _setup_schema(self):
        """Create simple schema for task tracking"""
        if not self.connected:
            return
        
        with self.driver.session() as session:
            # Simple constraints and indexes
            try:
                session.run("CREATE CONSTRAINT task_name IF NOT EXISTS FOR (t:Task) REQUIRE t.name IS UNIQUE")
                session.run("CREATE INDEX task_session IF NOT EXISTS FOR (t:Task) ON t.session_name")
                session.run("CREATE INDEX result_timestamp IF NOT EXISTS FOR (r:Result) ON r.timestamp")
            except Exception as e:
                print(f"Schema setup note: {e}")
    
    def store_task_result(self, result: TaskResult):
        """Store task execution result"""
        if self.connected:
            self._store_neo4j(result)
        else:
            self._store_memory(result)
    
    def _store_neo4j(self, result: TaskResult):
        """Store in Neo4j"""
        with self.driver.session() as session:
            # Create or update task node
            session.run("""
                MERGE (t:Task {name: $name, session_name: $session})
                SET t.last_run = $timestamp,
                    t.total_runs = coalesce(t.total_runs, 0) + 1,
                    t.success_count = coalesce(t.success_count, 0) + $success_increment
                
                CREATE (r:Result {
                    task_name: $name,
                    success: $success,
                    output: $output,
                    execution_time: $exec_time,
                    timestamp: $timestamp,
                    session_name: $session,
                    error: $error
                })
                
                CREATE (t)-[:EXECUTED]->(r)
            """, {
                "name": result.task_name,
                "session": self.session_name,
                "timestamp": datetime.now().isoformat(),
                "success": result.success,
                "output": json.dumps(result.output) if result.output else None,
                "exec_time": result.execution_time,
                "error": result.error,
                "success_increment": 1 if result.success else 0
            })
    
    def _store_memory(self, result: TaskResult):
        """Store in memory fallback"""
        task_name = result.task_name
        
        # Update task stats
        if task_name not in self.memory_store['tasks']:
            self.memory_store['tasks'][task_name] = {
                'total_runs': 0,
                'success_count': 0,
                'last_run': None
            }
        
        task_stats = self.memory_store['tasks'][task_name]
        task_stats['total_runs'] += 1
        task_stats['last_run'] = datetime.now().isoformat()
        
        if result.success:
            task_stats['success_count'] += 1
        
        # Store result
        self.memory_store['results'].append(asdict(result))
    
    def get_task_success_rate(self, task_name: str) -> float:
        """Get success rate for a task"""
        if self.connected:
            return self._get_success_rate_neo4j(task_name)
        else:
            return self._get_success_rate_memory(task_name)
    
    def _get_success_rate_neo4j(self, task_name: str) -> float:
        """Get success rate from Neo4j"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Task {name: $name, session_name: $session})
                RETURN t.success_count as successes, t.total_runs as total
            """, {"name": task_name, "session": self.session_name})
            
            record = result.single()
            if record and record["total"] > 0:
                return record["successes"] / record["total"]
            return 0.0
    
    def _get_success_rate_memory(self, task_name: str) -> float:
        """Get success rate from memory"""
        if task_name in self.memory_store['tasks']:
            stats = self.memory_store['tasks'][task_name]
            if stats['total_runs'] > 0:
                return stats['success_count'] / stats['total_runs']
        return 0.0
    
    def store_task_dependency(self, parent_task: str, child_task: str):
        """Store task dependency relationship"""
        if self.connected:
            with self.driver.session() as session:
                session.run("""
                    MERGE (parent:Task {name: $parent, session_name: $session})
                    MERGE (child:Task {name: $child, session_name: $session})
                    MERGE (parent)-[:DEPENDS_ON]->(child)
                """, {
                    "parent": parent_task,
                    "child": child_task,
                    "session": self.session_name
                })
    
    def get_task_dependencies(self, task_name: str) -> List[str]:
        """Get dependencies for a task"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Task {name: $name, session_name: $session})-[:DEPENDS_ON]->(dep:Task)
                RETURN dep.name as dependency
            """, {"name": task_name, "session": self.session_name})
            
            return [record["dependency"] for record in result]
    
    def find_similar_task_patterns(self, context: Dict[str, Any], limit: int = 5) -> List[Dict]:
        """Find tasks that succeeded in similar contexts"""
        if not self.connected:
            return []
        
        # Simple pattern matching based on context keys
        context_keys = set(context.keys())
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Result {success: true, session_name: $session})
                WHERE r.output IS NOT NULL
                RETURN r.task_name as task, r.output as output, r.timestamp as timestamp
                ORDER BY r.timestamp DESC
                LIMIT $limit
            """, {"session": self.session_name, "limit": limit})
            
            patterns = []
            for record in result:
                patterns.append({
                    "task_name": record["task"],
                    "output": record["output"],
                    "timestamp": record["timestamp"]
                })
            
            return patterns
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if self.connected:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (t:Task {session_name: $session})
                    RETURN count(t) as total_tasks,
                           sum(t.total_runs) as total_executions,
                           sum(t.success_count) as total_successes
                """, {"session": self.session_name})
                
                record = result.single()
                if record:
                    total_executions = record["total_executions"] or 0
                    total_successes = record["total_successes"] or 0
                    success_rate = total_successes / total_executions if total_executions > 0 else 0
                    
                    return {
                        "connected": True,
                        "total_tasks": record["total_tasks"],
                        "total_executions": total_executions,
                        "overall_success_rate": success_rate,
                        "session": self.session_name
                    }
        
        # Memory fallback stats
        total_tasks = len(self.memory_store['tasks'])
        total_runs = sum(t['total_runs'] for t in self.memory_store['tasks'].values())
        total_successes = sum(t['success_count'] for t in self.memory_store['tasks'].values())
        
        return {
            "connected": False,
            "total_tasks": total_tasks,
            "total_executions": total_runs,
            "overall_success_rate": total_successes / total_runs if total_runs > 0 else 0,
            "session": self.session_name
        }
    
    def close(self):
        """Close connections"""
        if self.driver:
            self.driver.close()

class TaskBasedAgent:
    """Simple task-based agent with function registry"""
    
    def __init__(self, session_name: str = "pokemon_agent"):
        self.memory = SimplifiedTaskMemory(session_name)
        self.tasks = {}  # Registry of available tasks
        self.execution_log = []
        
        # Register common Pokemon tasks
        self._register_default_tasks()
    
    def register_task(self, task: TaskNode):
        """Register a task function"""
        self.tasks[task.name] = task
        
        # Store dependencies in memory
        for dep in task.dependencies:
            self.memory.store_task_dependency(task.name, dep)
    
    def _register_default_tasks(self):
        """Register default Pokemon game tasks"""
        
        def check_pokemon_health(pokemon_data):
            """Check Pokemon health status"""
            if not pokemon_data or 'hp' not in pokemon_data:
                return {"status": "unknown", "percent": 0.0}
            
            # Parse HP string like "8/26"
            hp_str = pokemon_data['hp']
            if '/' in hp_str:
                current, maximum = map(int, hp_str.split('/'))
                percent = current / maximum
                
                return {
                    "status": "critical" if percent < 0.3 else "good",
                    "percent": percent,
                    "needs_healing": percent < 0.15,
                    "current_hp": current,
                    "max_hp": maximum
                }
            
            return {"status": "unknown", "percent": 0.0}
        
        def decide_next_move(context):
            """Decide next move based on battle context"""
            our_pokemon = context.get('our_pokemon', {})
            enemy_pokemon = context.get('enemy_pokemon', {})
            
            health = check_pokemon_health(our_pokemon)
            our_level = our_pokemon.get('level', 1)
            enemy_level = enemy_pokemon.get('level', 1)
            level_advantage = our_level / enemy_level if enemy_level > 0 else 1
            
            if health['needs_healing']:
                return {"action": "heal", "reasoning": "Critical HP - need healing"}
            elif level_advantage > 2.0:
                return {"action": "attack_any", "reasoning": "Major level advantage - finish quickly"}
            else:
                return {"action": "attack_optimal", "reasoning": "Use type effectiveness"}
        
        def find_strongest_move(moves, enemy_type=None):
            """Find the strongest available move"""
            if not moves:
                return None
            
            # Simple heuristic: prefer non-status moves
            damage_moves = [m for m in moves if not m.get('name', '').upper() in ['GROWL', 'LEER', 'TAIL WHIP']]
            
            if damage_moves:
                return damage_moves[0]  # Return first damage move
            else:
                return moves[0]  # Fallback to any move
        
        def play_next_move(move_choice, cursor_position="FIGHT"):
            """Convert move decision to button presses"""
            if move_choice == "heal":
                return ["right", "a"]  # Navigate to BAG
            elif cursor_position == "FIGHT":
                return ["a"]  # Select FIGHT
            else:
                return ["a"]  # Default action
        
        # Register tasks
        self.register_task(TaskNode("check_pokemon_health", check_pokemon_health))
        self.register_task(TaskNode("decide_next_move", decide_next_move, ["check_pokemon_health"]))
        self.register_task(TaskNode("find_strongest_move", find_strongest_move))
        self.register_task(TaskNode("play_next_move", play_next_move, ["decide_next_move"]))
    
    def execute_task(self, task_name: str, **kwargs) -> TaskResult:
        """Execute a task and store result in memory"""
        if task_name not in self.tasks:
            return TaskResult(
                task_name=task_name,
                success=False,
                output=None,
                execution_time=0.0,
                error=f"Task '{task_name}' not found"
            )
        
        task = self.tasks[task_name]
        start_time = time.time()
        
        try:
            # Execute task function
            output = task.func(**kwargs)
            execution_time = time.time() - start_time
            
            result = TaskResult(
                task_name=task_name,
                success=True,
                output=output,
                execution_time=execution_time,
                context=kwargs
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TaskResult(
                task_name=task_name,
                success=False,
                output=None,
                execution_time=execution_time,
                error=str(e),
                context=kwargs
            )
        
        # Store result in memory
        self.memory.store_task_result(result)
        self.execution_log.append(result)
        
        return result
    
    def execute_battle_sequence(self, battle_context: Dict[str, Any]) -> List[str]:
        """Execute complete battle decision sequence"""
        
        # Step 1: Check Pokemon health
        health_result = self.execute_task("check_pokemon_health", 
                                        pokemon_data=battle_context.get('our_pokemon', {}))
        
        # Step 2: Decide next move
        decision_result = self.execute_task("decide_next_move", context=battle_context)
        
        # Step 3: Convert to button presses
        button_result = self.execute_task("play_next_move", 
                                        move_choice=decision_result.output.get('action', 'attack'),
                                        cursor_position=battle_context.get('cursor_on', 'FIGHT'))
        
        # Return button sequence
        if button_result.success:
            return button_result.output
        else:
            return ["a"]  # Default fallback
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get agent task execution statistics"""
        stats = self.memory.get_memory_stats()
        stats['registered_tasks'] = list(self.tasks.keys())
        stats['recent_executions'] = len(self.execution_log)
        
        return stats
    
    def close(self):
        """Clean shutdown"""
        self.memory.close()