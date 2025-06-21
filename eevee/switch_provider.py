#!/usr/bin/env python3
"""
Provider Switching Demonstration Script
Shows how to easily switch between Gemini and Mistral providers using environment variables
"""

import os
import sys
from pathlib import Path

# Add project root to path
eevee_root = Path(__file__).parent
project_root = eevee_root.parent
sys.path.append(str(project_root))
sys.path.append(str(eevee_root))

from dotenv import load_dotenv

def demo_current_configuration():
    """Demonstrate current provider configuration"""
    print("🔧 Current Provider Configuration")
    print("=" * 50)
    
    from provider_config import get_provider_config
    
    config = get_provider_config(verbose=True)
    validation = config.validate_configuration()
    
    if not validation['valid']:
        print("❌ Configuration has errors:")
        for error in validation['errors']:
            print(f"   • {error}")
        return False
    
    if validation['warnings']:
        print("⚠️ Configuration warnings:")
        for warning in validation['warnings']:
            print(f"   • {warning}")
    
    return True

def demo_llm_api_with_current_config():
    """Demonstrate LLM API usage with current configuration"""
    print("\n🤖 Testing LLM API with Current Configuration")
    print("=" * 50)
    
    try:
        from provider_config import create_llm_manager_with_env_config
        from llm_api import call_llm
        
        # Create LLM manager with environment configuration
        manager = create_llm_manager_with_env_config()
        
        if not manager:
            print("❌ Failed to create LLM manager")
            return False
        
        print(f"✅ LLM Manager created successfully")
        print(f"📋 Available providers: {manager.get_available_providers()}")
        print(f"🎯 Current provider: {manager.current_provider}")
        
        # Test a simple API call
        print("\n🧪 Testing simple API call...")
        response = call_llm(
            prompt="What is 2+2? Answer with just the number.",
            max_tokens=50
        )
        
        if response.error:
            print(f"❌ API call failed: {response.error}")
            return False
        
        print(f"✅ API Response: '{response.text.strip()}'")
        print(f"🔧 Provider used: {response.provider}")
        print(f"🔧 Model used: {response.model}")
        print(f"⏱️ Response time: {response.response_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM API test failed: {e}")
        return False

def demo_provider_switching():
    """Demonstrate runtime provider switching"""
    print("\n🔄 Runtime Provider Switching Demo")
    print("=" * 50)
    
    try:
        from provider_config import get_provider_config
        from llm_api import call_llm
        
        config = get_provider_config()
        available_providers = config.get_available_providers()
        
        print(f"Available providers: {available_providers}")
        
        if len(available_providers) < 2:
            print("⚠️ Need at least 2 providers for switching demo")
            return True
        
        # Test with each provider
        for provider in available_providers:
            print(f"\n🎯 Testing with {provider.upper()} provider...")
            
            response = call_llm(
                prompt=f"You are using {provider}. Say hello in one sentence.",
                provider=provider,
                max_tokens=50
            )
            
            if response.error:
                print(f"❌ {provider} failed: {response.error}")
            else:
                print(f"✅ {provider}: {response.text.strip()}")
                print(f"   Model: {response.model}, Time: {response.response_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider switching demo failed: {e}")
        return False

def demo_pokemon_specific_usage():
    """Demonstrate Pokemon-specific model selection"""
    print("\n🎮 Pokemon-Specific Model Selection Demo")
    print("=" * 50)
    
    try:
        from provider_config import get_provider_config
        
        config = get_provider_config()
        
        # Show model selection for different Pokemon tasks
        tasks = [
            ("Template Selection", "template_selection", False),
            ("Gameplay Decisions", "gameplay", False),
            ("Screenshot Analysis", "vision", True),
            ("Battle Analysis", "gameplay", False)
        ]
        
        for task_name, task_type, has_vision in tasks:
            model = config.get_model_for_task(task_type, has_vision)
            print(f"🎯 {task_name}: {model}")
        
        # Get Eevee configuration
        eevee_config = config.get_eevee_config()
        print(f"\n📋 EeveeAgent Configuration:")
        for key, value in eevee_config.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pokemon usage demo failed: {e}")
        return False

def demo_easy_provider_switching_commands():
    """Show examples of easy provider switching"""
    print("\n💡 Easy Provider Switching Examples")
    print("=" * 50)
    
    print("🔧 To switch to Mistral for everything:")
    print("   export LLM_PROVIDER=mistral")
    print("   export TEMPLATE_SELECTION_MODEL=mistral-large-latest")
    print("   export GAMEPLAY_MODEL=pixtral-12b-2409")
    
    print("\n🔧 To switch to Gemini for everything:")
    print("   export LLM_PROVIDER=gemini")
    print("   export TEMPLATE_SELECTION_MODEL=gemini-2.0-flash-exp")
    print("   export GAMEPLAY_MODEL=gemini-2.0-flash-exp")
    
    print("\n🔧 For hybrid setup (Mistral vision + Gemini text):")
    print("   export LLM_PROVIDER=gemini")
    print("   export TEMPLATE_SELECTION_MODEL=gemini-2.0-flash-exp")
    print("   export GAMEPLAY_MODEL=pixtral-12b-2409")
    
    print("\n🔧 To enable auto-fallback between providers:")
    print("   export LLM_PROVIDER=gemini")
    print("   export FALLBACK_PROVIDER=mistral")
    print("   export AUTO_FALLBACK=true")
    
    print("\n💾 Make changes permanent by editing .env file:")
    print("   nano eevee/.env")
    
    return True

def main():
    """Main demonstration function"""
    print("🚀 Eevee Provider Switching Demonstration")
    print("=" * 60)
    
    # Load environment variables
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    demos = [
        ("Current Configuration", demo_current_configuration),
        ("LLM API with Current Config", demo_llm_api_with_current_config),
        ("Provider Switching", demo_provider_switching),
        ("Pokemon-Specific Usage", demo_pokemon_specific_usage),
        ("Easy Switching Commands", demo_easy_provider_switching_commands)
    ]
    
    success_count = 0
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*20} {demo_name} {'='*20}")
        try:
            success = demo_func()
            if success:
                success_count += 1
                print(f"✅ {demo_name} completed successfully")
            else:
                print(f"⚠️ {demo_name} completed with issues")
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
    
    print(f"\n🏁 Demonstration Results: {success_count}/{len(demos)} demos completed successfully")
    
    if success_count == len(demos):
        print("🎉 All provider switching features working correctly!")
    else:
        print("⚠️ Some features may need attention")

if __name__ == "__main__":
    main()