#!/usr/bin/env python3
"""
Test script to check if our Pokemon dataset can be loaded with Hugging Face datasets library
"""

import json
import os
from pathlib import Path

def test_huggingface_dataset_loading():
    """Test if our dataset can be loaded with load_dataset"""
    print("🧪 Testing Hugging Face dataset loading compatibility...")
    
    # First, let's try to import the datasets library
    try:
        from datasets import load_dataset, Dataset
        print("✅ datasets library available")
    except ImportError:
        print("❌ datasets library not installed. Install with: pip install datasets")
        return False
    
    # Our dataset path
    dataset_path = "training_data/pokemon_grid_dataset_final.jsonl"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset file not found: {dataset_path}")
        return False
    
    print(f"📁 Dataset file found: {dataset_path}")
    
    # Method 1: Try loading directly as JSONL
    print("\n🔄 Method 1: Loading as JSONL...")
    try:
        dataset = load_dataset('json', data_files=dataset_path, split='train')
        print(f"✅ Successfully loaded dataset with {len(dataset)} samples")
        print(f"📊 Dataset columns: {dataset.column_names}")
        
        # Check first sample
        sample = dataset[0]
        print(f"🔍 First sample keys: {list(sample.keys())}")
        print(f"📝 Sample structure:")
        for key, value in sample.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {type(value).__name__} (length: {len(value)})")
            else:
                print(f"  {key}: {type(value).__name__} = {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: Try loading with explicit schema
    print("\n🔄 Method 2: Loading with manual Dataset creation...")
    try:
        # Load JSONL manually first
        data = []
        with open(dataset_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        
        # Create dataset from list
        dataset = Dataset.from_list(data)
        print(f"✅ Successfully created dataset with {len(dataset)} samples")
        print(f"📊 Dataset columns: {dataset.column_names}")
        
        # Check if image paths exist
        sample = dataset[0]
        image_path = sample['image']
        if os.path.exists(image_path):
            print(f"✅ Image file exists: {image_path}")
        else:
            print(f"⚠️  Image file not found: {image_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    return False

def compare_with_llava_format():
    """Compare our format with LLaVa format"""
    print("\n🔍 Comparing with LLaVa dataset format...")
    
    # Our format
    dataset_path = "training_data/pokemon_grid_dataset_final.jsonl"
    if os.path.exists(dataset_path):
        with open(dataset_path, 'r') as f:
            our_sample = json.loads(f.readline().strip())
        
        print("📱 Our Pokemon dataset format:")
        print(f"  Keys: {list(our_sample.keys())}")
        print(f"  image: {type(our_sample.get('image', 'missing'))}")
        print(f"  context: {type(our_sample.get('context', 'missing'))}")
        print(f"  question: {type(our_sample.get('question', 'missing'))}")
        print(f"  output: {type(our_sample.get('output', 'missing'))}")
        print(f"  metadata: {type(our_sample.get('metadata', 'missing'))}")
    
    # Expected LLaVa format (based on documentation)
    print("\n📚 Expected LLaVa format:")
    print("  Keys: ['image', 'conversations']")
    print("  image: <PIL.Image>")
    print("  conversations: List[Dict] with 'from' and 'value' keys")
    
    print("\n💡 Conversion needed:")
    print("  ✅ image: Direct mapping (need to load as PIL Image)")
    print("  🔄 conversations: Need to transform context+question+output")
    print("  📝 Our rich metadata can be preserved in conversations")

def suggest_conversion_approach():
    """Suggest how to convert our format"""
    print("\n🛠️  Suggested conversion approach:")
    
    conversion_code = '''
def convert_pokemon_to_llava_format(sample):
    """Convert Pokemon dataset sample to LLaVa format"""
    from PIL import Image
    
    # Load image
    image = Image.open(sample['image'])
    
    # Create conversations format
    conversations = [
        {
            "from": "human",
            "value": f"{sample['context']}\\n\\n{sample['question']}"
        },
        {
            "from": "gpt", 
            "value": sample['output']
        }
    ]
    
    return {
        "image": image,
        "conversations": conversations,
        # Optionally preserve metadata
        "metadata": sample.get('metadata', {})
    }
'''
    
    print(conversion_code)

if __name__ == "__main__":
    print("🔬 Pokemon Dataset Compatibility Test\n")
    
    success = test_huggingface_dataset_loading()
    compare_with_llava_format()
    suggest_conversion_approach()
    
    if success:
        print("\n🎉 SUCCESS: Dataset can be loaded with Hugging Face datasets!")
        print("💡 Next steps: Test with actual training pipeline")
    else:
        print("\n⚠️  Dataset needs conversion for optimal compatibility")
        print("💡 Consider using the suggested conversion approach")