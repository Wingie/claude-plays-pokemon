# TaskExecutor Fix Specification

## Problem Analysis

**Error**: `'TaskExecutor' object has no attribute 'execute_task'`

**Root Cause**: Method name mismatch between caller and implementation:
- `run_eevee.py:2811` calls: `eevee.task_executor.execute_task(task, max_steps=20)`
- `task_executor.py:51` provides: `execute_plan(execution_plan, max_steps=50)`

## Current State

### TaskExecutor Methods (task_executor.py)
- ✅ `execute_plan(execution_plan, max_steps)` - Exists
- ❌ `execute_task(task, max_steps)` - Missing

### Caller Expectations (run_eevee.py)
- Expects: `execute_task(task_string, max_steps=int) -> Dict`
- Task input: Simple string like "test compact memory"
- Expected output: Execution result dictionary

## Fix Options

### Option 1: Add execute_task() method (Recommended)
```python
def execute_task(self, task: str, max_steps: int = 20) -> Dict[str, Any]:
    """
    Execute a task from string description
    
    Args:
        task: Task description string
        max_steps: Maximum execution steps
        
    Returns:
        Execution result dictionary
    """
    # 1. Convert task string to execution plan using prompt_manager
    # 2. Call existing execute_plan() method
    # 3. Return formatted result
```

### Option 2: Update caller to use execute_plan()
- More complex: Requires task analysis and plan creation in run_eevee.py
- Less clean separation of concerns

## Implementation Plan

### Step 1: Add execute_task() wrapper method
1. Create `execute_task()` method in `TaskExecutor`
2. Use `task_analysis` prompt template to convert task string to plan
3. Call existing `execute_plan()` method
4. Format and return results

### Step 2: Test the integration
1. Run the test command to verify fix
2. Ensure memory integration works correctly

## Code Structure

```python
class TaskExecutor:
    def execute_task(self, task: str, max_steps: int = 20) -> Dict[str, Any]:
        """Main entry point for task execution"""
        try:
            # Step 1: Analyze task and create plan
            execution_plan = self._create_plan_from_task(task)
            
            # Step 2: Execute the plan  
            result = self.execute_plan(execution_plan, max_steps)
            
            # Step 3: Format result
            return {
                "success": result.get("success", False),
                "status": result.get("status", "unknown"),
                "steps_completed": result.get("steps_completed", 0),
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "steps_completed": 0
            }
    
    def _create_plan_from_task(self, task: str) -> Dict[str, Any]:
        """Convert task string to execution plan using AI"""
        # Use task_analysis prompt template
        # Return structured execution plan
```

## Dependencies

- ✅ `prompt_manager.py` - Has `task_analysis` template
- ✅ `execute_plan()` method - Already implemented
- ✅ Error handling patterns - Already established

## Success Criteria

1. ✅ `python run_eevee.py --task "test compact memory" --max-turns 1` runs without AttributeError
2. ✅ Memory integration works correctly
3. ✅ Task execution returns proper result dictionary
4. ✅ No breaking changes to existing functionality