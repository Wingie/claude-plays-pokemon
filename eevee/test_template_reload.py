#!/usr/bin/env python3
"""
Test script to verify template reloading functionality
"""

import sys
from pathlib import Path
import yaml

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from prompt_manager import PromptManager

def test_template_reload():
    """Test that templates can be reloaded after updates"""
    
    print("🧪 Testing Template Reload Functionality")
    print("="*60)
    
    # Initialize prompt manager
    pm = PromptManager()
    
    # Get initial versions
    print("\n📌 Initial template versions:")
    versions_before = pm.get_template_versions()
    for template, version in versions_before.items():
        print(f"   {template}: v{version}")
    
    # Manually update a template version in the YAML file for testing
    base_prompts_file = pm.prompts_dir / "base" / "base_prompts.yaml"
    
    # Load current templates
    with open(base_prompts_file, 'r') as f:
        templates = yaml.safe_load(f)
    
    # Show current battle_analysis version
    if 'battle_analysis' in templates:
        current_version = templates['battle_analysis'].get('version', '1.0')
        print(f"\n🎯 Current battle_analysis version in YAML: {current_version}")
    
    # Test reload functionality
    print("\n🔄 Reloading templates...")
    pm.reload_templates()
    
    # Get versions after reload
    print("\n📌 Template versions after reload:")
    versions_after = pm.get_template_versions()
    for template, version in versions_after.items():
        print(f"   {template}: v{version}")
    
    # Test usage logging
    print("\n📊 Testing usage logging:")
    print(pm.get_usage_summary())
    
    print("\n✅ Template reload test complete!")

if __name__ == "__main__":
    test_template_reload()