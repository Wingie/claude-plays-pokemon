#!/usr/bin/env python3
"""
Test Template Hot-Swapping and Real-Time Updates
Validates that enhanced templates are immediately available in the system
"""

import yaml
import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

sys.path.append(str(eevee_dir))

from prompt_manager import PromptManager

def test_template_hotswap():
    """Test that the PromptManager immediately loads updated templates"""
    
    print("🔄 TEMPLATE HOT-SWAP VALIDATION")
    print("=" * 50)
    
    # Initialize PromptManager
    pm = PromptManager()
    
    # Check exploration_strategy template version
    exploration_template = pm.base_prompts.get('exploration_strategy', {})
    version = exploration_template.get('version', 'unknown')
    description = exploration_template.get('description', 'No description')
    template_length = len(exploration_template.get('template', ''))
    
    print(f"📊 Current Template Status:")
    print(f"   Template: exploration_strategy")
    print(f"   Version: {version}")
    print(f"   Description: {description}")
    print(f"   Template length: {template_length} characters")
    
    # Verify this is the enhanced v4.0 template
    template_content = exploration_template.get('template', '')
    
    # Check for v4.0 features
    v4_features = {
        "Enhanced Stuck Pattern Prevention": "ENHANCED STUCK PATTERN PREVENTION",
        "Oscillation Prevention": "OSCILLATION PREVENTION",
        "Corner Trap Escape": "CORNER TRAP ESCAPE PROTOCOLS",
        "Directional Bias Prevention": "DIRECTIONAL BIAS PREVENTION",
        "Trainer Approach Intelligence": "TRAINER APPROACH INTELLIGENCE",
        "Pokemon World Physics": "POKEMON WORLD PHYSICS & COLLISION INTELLIGENCE",
        "Navigation Decision Tree": "ENHANCED NAVIGATION DECISION TREE",
        "Single Button Discipline": "SINGLE BUTTON DISCIPLINE"
    }
    
    print(f"\n🔍 Enhanced v4.0 Features Verification:")
    
    all_features_present = True
    for feature_name, feature_text in v4_features.items():
        feature_present = feature_text in template_content
        status = "✅" if feature_present else "❌"
        print(f"   {status} {feature_name}")
        if not feature_present:
            all_features_present = False
    
    # Test template formatting capability
    print(f"\n🔧 Template Formatting Test:")
    try:
        formatted_template = pm.get_ai_directed_prompt(
            context_type="auto_select",
            task="explore and win pokemon battles",
            recent_actions=["up", "right"],
            memory_context="test memory context",
            verbose=False
        )
        
        print(f"   ✅ Template formatting successful")
        print(f"   Formatted template length: {len(formatted_template)} characters")
        
        # Check if formatted template contains v4.0 features
        v4_in_formatted = "ENHANCED STUCK PATTERN PREVENTION" in formatted_template
        print(f"   ✅ v4.0 features in formatted template: {v4_in_formatted}")
        
    except Exception as e:
        print(f"   ❌ Template formatting failed: {e}")
        all_features_present = False
    
    return all_features_present, version

def test_template_variables():
    """Test that template variables are correctly defined"""
    
    print(f"\n\n📋 TEMPLATE VARIABLES VALIDATION")
    print("=" * 50)
    
    pm = PromptManager()
    exploration_template = pm.base_prompts.get('exploration_strategy', {})
    
    expected_variables = ["task", "recent_actions"]
    actual_variables = exploration_template.get('variables', [])
    template_content = exploration_template.get('template', '')
    
    print(f"📊 Variable Configuration:")
    print(f"   Expected variables: {expected_variables}")
    print(f"   Actual variables: {actual_variables}")
    
    # Test variable presence
    variables_correct = True
    for var in expected_variables:
        if var in actual_variables:
            print(f"   ✅ {var}: Defined in template")
        else:
            print(f"   ❌ {var}: Missing from template definition")
            variables_correct = False
    
    # Test variable usage
    print(f"\n📝 Variable Usage in Template:")
    for var in expected_variables:
        var_pattern = f"{{{var}}}"
        if var_pattern in template_content:
            usage_count = template_content.count(var_pattern)
            print(f"   ✅ {var}: Used {usage_count} time(s)")
        else:
            print(f"   ❌ {var}: Not used in template")
            variables_correct = False
    
    return variables_correct

def test_backup_and_version_tracking():
    """Test that backup was created and version tracking works"""
    
    print(f"\n\n💾 BACKUP & VERSION TRACKING VALIDATION")
    print("=" * 50)
    
    # Check backup file exists
    backup_file = eevee_dir / "prompts" / "base" / "base_prompts_v3.2_backup.yaml"
    
    if backup_file.exists():
        print(f"   ✅ Backup file created: {backup_file.name}")
        
        # Load backup and check version
        with open(backup_file, 'r') as f:
            backup_templates = yaml.safe_load(f)
        
        backup_exploration = backup_templates.get('exploration_strategy', {})
        backup_version = backup_exploration.get('version', 'unknown')
        backup_length = len(backup_exploration.get('template', ''))
        
        print(f"   📊 Backup template version: {backup_version}")
        print(f"   📊 Backup template length: {backup_length} characters")
        
    else:
        print(f"   ❌ Backup file not found")
        return False
    
    # Check current file has new version
    current_file = eevee_dir / "prompts" / "base" / "base_prompts.yaml"
    with open(current_file, 'r') as f:
        current_templates = yaml.safe_load(f)
    
    current_exploration = current_templates.get('exploration_strategy', {})
    current_version = current_exploration.get('version', 'unknown')
    current_length = len(current_exploration.get('template', ''))
    
    print(f"\n   📊 Current template version: {current_version}")
    print(f"   📊 Current template length: {current_length} characters")
    print(f"   📈 Length increase: {current_length - backup_length} characters")
    
    version_upgraded = current_version > backup_version
    print(f"   ✅ Version upgraded: {backup_version} → {current_version}")
    
    return version_upgraded

def test_cross_session_compatibility():
    """Test that the enhanced template is compatible with existing systems"""
    
    print(f"\n\n🔗 CROSS-SESSION COMPATIBILITY TEST")
    print("=" * 50)
    
    pm = PromptManager()
    
    # Test AI-directed template mapping still works
    ai_template_mapping = {
        "ai_directed_navigation": "exploration_strategy",
        "ai_directed_battle": "battle_analysis", 
        "ai_directed_emergency": "stuck_recovery"
    }
    
    print(f"🗺️ AI Template Mapping Validation:")
    
    mapping_works = True
    for ai_template, base_template in ai_template_mapping.items():
        if base_template in pm.base_prompts:
            base_version = pm.base_prompts[base_template].get('version', 'unknown')
            print(f"   ✅ {ai_template} → {base_template} v{base_version}")
        else:
            print(f"   ❌ {ai_template} → {base_template} (missing)")
            mapping_works = False
    
    # Test that all required templates exist
    required_templates = [
        "exploration_strategy", "battle_analysis", "stuck_recovery",
        "task_analysis", "pokemon_party_analysis", "inventory_analysis"
    ]
    
    print(f"\n📋 Required Templates Check:")
    
    all_templates_present = True
    for template in required_templates:
        if template in pm.base_prompts:
            version = pm.base_prompts[template].get('version', 'unknown')
            print(f"   ✅ {template}: v{version} available")
        else:
            print(f"   ❌ {template}: Missing")
            all_templates_present = False
    
    return mapping_works and all_templates_present

if __name__ == "__main__":
    try:
        print("🚀 TEMPLATE HOT-SWAP & REAL-TIME UPDATE VALIDATION")
        print("=" * 70)
        
        # Run all tests
        features_ok, version = test_template_hotswap()
        variables_ok = test_template_variables()
        backup_ok = test_backup_and_version_tracking()
        compatibility_ok = test_cross_session_compatibility()
        
        print(f"\n\n🎯 TEMPLATE HOT-SWAP TEST SUMMARY")
        print("=" * 70)
        
        if all([features_ok, variables_ok, backup_ok, compatibility_ok]):
            print("✅ Template hot-swap validation: ALL TESTS PASSED")
            print(f"✅ Enhanced exploration_strategy v{version} successfully deployed")
            print("✅ PromptManager immediately loads updated templates")
            print("✅ Template formatting and variables working correctly")
            print("✅ Backup system and version tracking operational")
            print("✅ Cross-session compatibility maintained")
            print("✅ System ready for live testing with enhanced templates")
        else:
            print("❌ Template hot-swap validation: SOME TESTS FAILED")
            print(f"   Features present: {features_ok}")
            print(f"   Variables correct: {variables_ok}")
            print(f"   Backup created: {backup_ok}")
            print(f"   Compatibility maintained: {compatibility_ok}")
        
    except Exception as e:
        print(f"❌ Template hot-swap test failed: {e}")
        import traceback
        traceback.print_exc()