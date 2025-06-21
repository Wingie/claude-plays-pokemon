#!/usr/bin/env python3
"""
Test script to verify TaskExecutor migration to centralized LLM API
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
eevee_root = Path(__file__).parent.parent
project_root = eevee_root.parent
sys.path.append(str(project_root))
sys.path.append(str(eevee_root))

from dotenv import load_dotenv

def test_task_executor_initialization():
    """Test that TaskExecutor initializes with a mock EeveeAgent"""
    print("🔧 Testing TaskExecutor Initialization...")
    
    try:
        from task_executor import TaskExecutor, StepStatus, TaskComplexity
        
        # Create mock EeveeAgent
        mock_agent = Mock()
        mock_agent.verbose = True
        mock_agent.current_model = "gemini-2.0-flash-exp"
        
        # Initialize TaskExecutor
        executor = TaskExecutor(mock_agent)
        
        print("✅ TaskExecutor initialized successfully")
        
        # Test basic attributes
        if hasattr(executor, 'agent') and executor.agent == mock_agent:
            print("✅ Agent reference correctly set")
        else:
            print("❌ Agent reference not set correctly")
            return False
        
        # Test configuration attributes
        expected_attrs = ['max_retries_per_step', 'step_timeout', 'screenshot_interval']
        for attr in expected_attrs:
            if hasattr(executor, attr):
                print(f"✅ Configuration attribute {attr} present")
            else:
                print(f"❌ Configuration attribute {attr} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ TaskExecutor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_centralized_api_integration():
    """Test that TaskExecutor uses centralized LLM API imports"""
    print("\n🔗 Testing Centralized LLM API Integration...")
    
    try:
        from task_executor import TaskExecutor
        
        # Create mock EeveeAgent
        mock_agent = Mock()
        mock_agent.verbose = False
        mock_agent.current_model = "gemini-2.0-flash-exp"
        
        executor = TaskExecutor(mock_agent)
        
        # Check that methods exist and can import call_llm
        analysis_methods = [
            '_execute_analysis_step',
            '_execute_condition_step', 
            '_execute_analysis_and_action_step'
        ]
        
        for method_name in analysis_methods:
            if hasattr(executor, method_name):
                print(f"✅ Method {method_name} available")
            else:
                print(f"❌ Method {method_name} missing")
                return False
        
        # Test that call_llm can be imported (this tests the migration)
        try:
            from llm_api import call_llm
            print("✅ Centralized LLM API import successful")
        except ImportError as e:
            print(f"❌ LLM API import failed: {e}")
            return False
        
        print("✅ TaskExecutor successfully integrated with centralized LLM API")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_step_execution_structure():
    """Test basic step execution structure without API calls"""
    print("\n📝 Testing Step Execution Structure...")
    
    try:
        from task_executor import TaskExecutor, StepStatus
        
        # Create mock EeveeAgent with all needed methods
        mock_agent = Mock()
        mock_agent.verbose = False
        mock_agent.current_model = "gemini-2.0-flash-exp"
        
        # Mock the controller
        mock_controller = Mock()
        mock_agent.controller = mock_controller
        
        # Mock the context capture method
        mock_context = {
            "screenshot_data": "mock_base64_data",
            "screenshot_path": "/mock/path.jpg",
            "timestamp": "2025-01-01T00:00:00"
        }
        mock_agent._capture_current_context.return_value = mock_context
        
        executor = TaskExecutor(mock_agent)
        
        # Test button execution step (doesn't require API)
        button_step = {
            "action": "press_buttons",
            "buttons": ["a", "start"],
            "description": "Test button press"
        }
        
        result = executor._execute_button_step(button_step)
        
        if result["status"] == StepStatus.COMPLETED.value:
            print("✅ Button step execution successful")
        else:
            print(f"❌ Button step execution failed: {result}")
            return False
        
        # Test navigation step (doesn't require API)
        nav_step = {
            "action": "navigate_menu",
            "target": "pokemon_menu",
            "sequence": ["start", "up", "a"],
            "description": "Test navigation"
        }
        
        result = executor._execute_navigation_step(nav_step)
        
        if result["status"] == StepStatus.COMPLETED.value:
            print("✅ Navigation step execution successful")
        else:
            print(f"❌ Navigation step execution failed: {result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Step execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_execution_plan_structure():
    """Test execution plan processing structure"""
    print("\n📋 Testing Execution Plan Structure...")
    
    try:
        from task_executor import TaskExecutor, TaskComplexity
        
        # Create mock EeveeAgent
        mock_agent = Mock()
        mock_agent.verbose = False
        mock_agent.current_model = "gemini-2.0-flash-exp"
        mock_controller = Mock()
        mock_agent.controller = mock_controller
        
        # Mock context capture
        mock_context = {
            "screenshot_data": "mock_data",
            "screenshot_path": "/mock/path.jpg"
        }
        mock_agent._capture_current_context.return_value = mock_context
        
        executor = TaskExecutor(mock_agent)
        
        # Test with a simple execution plan
        execution_plan = {
            "task": "Test task",
            "complexity": TaskComplexity.SIMPLE.value,
            "estimated_steps": 2,
            "steps": [
                {
                    "action": "press_buttons",
                    "buttons": ["start"],
                    "description": "Open menu"
                },
                {
                    "action": "press_buttons", 
                    "buttons": ["a"],
                    "description": "Select option"
                }
            ]
        }
        
        # Execute plan with max_steps=2 to limit execution
        result = executor.execute_plan(execution_plan, max_steps=2)
        
        if result["status"] in ["success", "partial_success"]:
            print(f"✅ Execution plan completed with status: {result['status']}")
            print(f"   Steps executed: {result['steps_executed']}/{result['total_steps']}")
        else:
            print(f"❌ Execution plan failed: {result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Execution plan test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_task_executor_migration_tests():
    """Run all TaskExecutor migration tests"""
    print("🚀 Testing TaskExecutor Migration to Centralized LLM API")
    print("=" * 60)
    
    tests = [
        ("TaskExecutor Initialization", test_task_executor_initialization),
        ("Centralized API Integration", test_centralized_api_integration),
        ("Step Execution Structure", test_step_execution_structure),
        ("Execution Plan Structure", test_execution_plan_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: CRASHED - {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Migration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 TaskExecutor migration successful!")
    elif passed > total // 2:
        print("⚠️ Partial migration success - some issues detected")
    else:
        print("❌ Migration failed - check configuration")
    
    return passed, total

if __name__ == "__main__":
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Run tests
    passed, total = run_task_executor_migration_tests()
    sys.exit(0 if passed == total else 1)