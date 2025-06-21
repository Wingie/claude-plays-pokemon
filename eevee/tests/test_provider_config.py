#!/usr/bin/env python3
"""
Test script to verify provider configuration system
"""

import os
import sys
from pathlib import Path

# Add project root to path
eevee_root = Path(__file__).parent.parent
project_root = eevee_root.parent
sys.path.append(str(project_root))
sys.path.append(str(eevee_root))

from dotenv import load_dotenv

def test_provider_config_initialization():
    """Test that ProviderConfig initializes correctly"""
    print("🔧 Testing ProviderConfig Initialization...")
    
    # Load environment variables
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    try:
        from provider_config import ProviderConfig
        
        # Initialize ProviderConfig
        config = ProviderConfig(verbose=False)
        
        print("✅ ProviderConfig initialized successfully")
        
        # Test basic attributes
        expected_attrs = [
            'primary_provider', 'fallback_provider', 'auto_fallback',
            'gemini_api_key', 'mistral_api_key', 'gemini_default', 'mistral_default'
        ]
        
        for attr in expected_attrs:
            if hasattr(config, attr):
                print(f"✅ Attribute {attr} present")
            else:
                print(f"❌ Attribute {attr} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ ProviderConfig test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_manager_config_generation():
    """Test LLM manager configuration generation"""
    print("\n📋 Testing LLM Manager Config Generation...")
    
    try:
        from provider_config import ProviderConfig
        
        config = ProviderConfig()
        llm_config = config.get_llm_manager_config()
        
        # Check required config keys
        required_keys = ['default_provider', 'fallback_provider', 'auto_fallback', 'gemini', 'mistral']
        
        for key in required_keys:
            if key in llm_config:
                print(f"✅ Config key {key} present")
            else:
                print(f"❌ Config key {key} missing")
                return False
        
        # Check nested provider configs
        for provider in ['gemini', 'mistral']:
            provider_config = llm_config[provider]
            required_sub_keys = ['api_key', 'circuit_breaker_reset_time', 'api_failure_threshold']
            
            for sub_key in required_sub_keys:
                if sub_key in provider_config:
                    print(f"✅ Provider {provider}.{sub_key} present")
                else:
                    print(f"❌ Provider {provider}.{sub_key} missing")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ LLM manager config test failed: {e}")
        return False

def test_eevee_config_generation():
    """Test EeveeAgent configuration generation"""
    print("\n🎮 Testing Eevee Config Generation...")
    
    try:
        from provider_config import ProviderConfig
        
        config = ProviderConfig()
        eevee_config = config.get_eevee_config()
        
        # Check required config keys
        required_keys = ['model', 'verbose', 'debug', 'template_selection_model', 'max_tokens']
        
        for key in required_keys:
            if key in eevee_config:
                print(f"✅ Eevee config key {key} present: {eevee_config[key]}")
            else:
                print(f"❌ Eevee config key {key} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Eevee config test failed: {e}")
        return False

def test_provider_availability_detection():
    """Test provider availability detection based on API keys"""
    print("\n🔍 Testing Provider Availability Detection...")
    
    try:
        from provider_config import ProviderConfig
        
        config = ProviderConfig()
        available_providers = config.get_available_providers()
        
        print(f"✅ Available providers detected: {available_providers}")
        
        # Test validation
        validation = config.validate_configuration()
        
        print(f"✅ Configuration validation: {'Valid' if validation['valid'] else 'Invalid'}")
        
        if validation['warnings']:
            print(f"⚠️ Warnings: {len(validation['warnings'])}")
            for warning in validation['warnings']:
                print(f"   • {warning}")
        
        if validation['errors']:
            print(f"❌ Errors: {len(validation['errors'])}")
            for error in validation['errors']:
                print(f"   • {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider availability test failed: {e}")
        return False

def test_model_selection_for_tasks():
    """Test model selection based on task type"""
    print("\n🤖 Testing Model Selection for Tasks...")
    
    try:
        from provider_config import ProviderConfig
        
        config = ProviderConfig()
        
        # Test different task types
        task_types = [
            ('template_selection', False),
            ('gameplay', False),
            ('vision', True),
            ('general', False)
        ]
        
        for task_type, has_vision in task_types:
            model = config.get_model_for_task(task_type, has_vision)
            print(f"✅ Task '{task_type}' (vision: {has_vision}) → Model: {model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model selection test failed: {e}")
        return False

def test_provider_switching():
    """Test runtime provider switching"""
    print("\n🔄 Testing Provider Switching...")
    
    try:
        from provider_config import ProviderConfig
        
        config = ProviderConfig()
        original_provider = config.primary_provider
        available_providers = config.get_available_providers()
        
        print(f"Original provider: {original_provider}")
        print(f"Available providers: {available_providers}")
        
        # Test switching to each available provider
        for provider in available_providers:
            success = config.switch_provider(provider)
            if success:
                print(f"✅ Successfully switched to {provider}")
                print(f"   Current provider: {config.primary_provider}")
            else:
                print(f"❌ Failed to switch to {provider}")
        
        # Test switching to unavailable provider
        unavailable_provider = 'invalid_provider'
        success = config.switch_provider(unavailable_provider)
        if not success:
            print(f"✅ Correctly rejected switch to unavailable provider: {unavailable_provider}")
        else:
            print(f"❌ Incorrectly allowed switch to unavailable provider: {unavailable_provider}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Provider switching test failed: {e}")
        return False

def test_global_config_functions():
    """Test global configuration utility functions"""
    print("\n🌐 Testing Global Config Functions...")
    
    try:
        from provider_config import get_provider_config, setup_eevee_with_env_config
        
        # Test global config instance
        config1 = get_provider_config()
        config2 = get_provider_config()
        
        if config1 is config2:
            print("✅ Global config singleton working correctly")
        else:
            print("❌ Global config singleton not working")
            return False
        
        # Test Eevee config setup
        eevee_config = setup_eevee_with_env_config()
        
        if isinstance(eevee_config, dict) and 'model' in eevee_config:
            print(f"✅ Eevee config setup successful: {eevee_config['model']}")
        else:
            print("❌ Eevee config setup failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Global config test failed: {e}")
        return False

def run_provider_config_tests():
    """Run all provider configuration tests"""
    print("🚀 Testing Provider Configuration System")
    print("=" * 60)
    
    tests = [
        ("ProviderConfig Initialization", test_provider_config_initialization),
        ("LLM Manager Config Generation", test_llm_manager_config_generation),
        ("Eevee Config Generation", test_eevee_config_generation),
        ("Provider Availability Detection", test_provider_availability_detection),
        ("Model Selection for Tasks", test_model_selection_for_tasks),
        ("Provider Switching", test_provider_switching),
        ("Global Config Functions", test_global_config_functions)
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
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Provider configuration system working perfectly!")
    elif passed > total // 2:
        print("⚠️ Most tests passed, system mostly functional")
    else:
        print("❌ Multiple failures detected, check configuration")
    
    return passed, total

if __name__ == "__main__":
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Run tests
    passed, total = run_provider_config_tests()
    sys.exit(0 if passed == total else 1)