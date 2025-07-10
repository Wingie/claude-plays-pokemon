#!/usr/bin/env python3
"""
Gemma Dataset Compatibility Test Script
Tests if our Pokemon dataset works directly with Gemma VLM fine-tuning using TRL
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dataset_loading():
    """Test loading our dataset with Hugging Face datasets library"""
    print("🧪 Testing Hugging Face dataset loading...")
    
    try:
        from datasets import load_dataset, Dataset, Image
        from PIL import Image as PILImage
        print("✅ Required libraries available")
    except ImportError as e:
        print(f"❌ Missing libraries: {e}")
        print("💡 Install with: pip install datasets transformers pillow")
        return False
    
    dataset_path = "training_data/pokemon_grid_dataset_final.jsonl"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset file not found: {dataset_path}")
        return False
    
    # Load dataset
    try:
        dataset = load_dataset('json', data_files=dataset_path, split='train')
        print(f"✅ Dataset loaded: {len(dataset)} samples")
        print(f"📊 Columns: {dataset.column_names}")
        return dataset
    except Exception as e:
        print(f"❌ Dataset loading failed: {e}")
        return False

def test_image_loading(dataset):
    """Test image loading and PIL conversion"""
    print("\n🖼️  Testing image loading...")
    
    try:
        from PIL import Image as PILImage
        
        # Test first sample
        sample = dataset[0]
        image_path = sample['image']
        
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
        
        # Load image
        image = PILImage.open(image_path)
        print(f"✅ Image loaded: {image.size} pixels, mode: {image.mode}")
        
        # Test conversion to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            print(f"✅ Converted to RGB mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Image loading failed: {e}")
        return False

def test_gemma_chat_format_conversion(dataset):
    """Test conversion to Gemma chat format"""
    print("\n💬 Testing Gemma chat format conversion...")
    
    def convert_to_gemma_format(sample):
        """Convert our format to Gemma chat format"""
        try:
            # Combine context and question as user message
            user_message = f"{sample['context']}\n\n{sample['question']}"
            
            # Create conversations in chat format
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": sample['output']}
            ]
            
            return {
                "image": sample['image'],
                "messages": messages,
                "metadata": sample.get('metadata', {})
            }
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return None
    
    # Test conversion on first few samples
    try:
        converted_samples = []
        for i in range(min(3, len(dataset))):
            sample = dataset[i]
            converted = convert_to_gemma_format(sample)
            if converted:
                converted_samples.append(converted)
        
        print(f"✅ Converted {len(converted_samples)} samples to chat format")
        
        # Show example
        if converted_samples:
            example = converted_samples[0]
            print("\n📝 Example converted sample:")
            print(f"  Image: {example['image']}")
            print(f"  Messages: {len(example['messages'])} messages")
            print(f"  User message length: {len(example['messages'][0]['content'])}")
            print(f"  Assistant response: {example['messages'][1]['content'][:100]}...")
        
        return converted_samples
        
    except Exception as e:
        print(f"❌ Chat format conversion failed: {e}")
        return []

def test_json_output_parsing(dataset):
    """Test parsing JSON outputs for training"""
    print("\n🔍 Testing JSON output parsing...")
    
    try:
        valid_outputs = 0
        total_samples = min(10, len(dataset))
        
        for i in range(total_samples):
            sample = dataset[i]
            output = sample['output']
            
            try:
                parsed = json.loads(output)
                required_fields = ['button', 'reasoning', 'context']
                
                if all(field in parsed for field in required_fields):
                    valid_outputs += 1
                else:
                    print(f"⚠️  Sample {i}: Missing required fields")
                    
            except json.JSONDecodeError:
                print(f"⚠️  Sample {i}: Invalid JSON")
        
        success_rate = valid_outputs / total_samples
        print(f"✅ JSON parsing success rate: {success_rate:.1%} ({valid_outputs}/{total_samples})")
        
        return success_rate > 0.9
        
    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")
        return False

def test_tokenization_compatibility():
    """Test tokenization with Gemma tokenizer"""
    print("\n🔤 Testing Gemma tokenizer compatibility...")
    
    try:
        from transformers import AutoTokenizer
        
        # Try to load Gemma tokenizer
        model_name = "google/gemma-2-2b-it"  # Using smaller model for testing
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print(f"✅ Loaded tokenizer: {model_name}")
        
        # Test sample text
        sample_text = """🎮 You are ASH KETCHUM with incredible memory and learning abilities.

**CURRENT MISSION:** enter the pokehealth center and heal your pokemon

**TEMPORAL GRID ANALYSIS:**
This is a 2x2 grid showing 4 consecutive Pokemon gameplay frames (~960ms total)

**RESPONSE FORMAT (MANDATORY JSON):**
```json
{
  "button": "action_name",
  "reasoning": "strategic_explanation", 
  "context": "situation_type",
  "scene_description": "detailed_scene_analysis"
}
```"""
        
        # Tokenize
        tokens = tokenizer.encode(sample_text)
        decoded = tokenizer.decode(tokens)
        
        print(f"✅ Tokenization test successful")
        print(f"  Original length: {len(sample_text)} chars")
        print(f"  Token count: {len(tokens)} tokens")
        print(f"  Tokens per char: {len(tokens)/len(sample_text):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tokenization test failed: {e}")
        print("💡 Note: This might be normal if Gemma models aren't cached locally")
        return False

def create_training_ready_dataset(dataset, output_path="training_data/pokemon_gemma_format.jsonl"):
    """Create a training-ready dataset in Gemma format"""
    print(f"\n🏗️  Creating training-ready dataset at {output_path}...")
    
    try:
        from PIL import Image as PILImage
        
        converted_count = 0
        total_count = len(dataset)
        
        with open(output_path, 'w') as f:
            for i, sample in enumerate(dataset):
                try:
                    # Verify image exists
                    if not os.path.exists(sample['image']):
                        print(f"⚠️  Skipping sample {i}: Image not found")
                        continue
                    
                    # Convert to Gemma format
                    user_message = f"{sample['context']}\n\n{sample['question']}"
                    
                    gemma_sample = {
                        "image": sample['image'],
                        "conversations": [
                            {"from": "human", "value": user_message},
                            {"from": "gpt", "value": sample['output']}
                        ],
                        "metadata": sample.get('metadata', {})
                    }
                    
                    # Write to file
                    f.write(json.dumps(gemma_sample) + '\n')
                    converted_count += 1
                    
                    if (i + 1) % 100 == 0:
                        print(f"  Progress: {i+1}/{total_count} samples processed")
                        
                except Exception as e:
                    print(f"⚠️  Error processing sample {i}: {e}")
                    continue
        
        success_rate = converted_count / total_count
        print(f"✅ Created training dataset: {converted_count}/{total_count} samples ({success_rate:.1%})")
        print(f"📁 Saved to: {output_path}")
        
        return output_path if success_rate > 0.95 else None
        
    except Exception as e:
        print(f"❌ Dataset creation failed: {e}")
        return None

def test_small_batch_loading(dataset_path=None):
    """Test loading a small batch for training simulation"""
    print("\n📦 Testing small batch loading...")
    
    if not dataset_path:
        dataset_path = "training_data/pokemon_gemma_format.jsonl"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Training dataset not found: {dataset_path}")
        return False
    
    try:
        from datasets import load_dataset
        from PIL import Image as PILImage
        
        # Load small subset
        dataset = load_dataset('json', data_files=dataset_path, split='train[:5]')
        print(f"✅ Loaded small batch: {len(dataset)} samples")
        
        # Test batch processing
        batch_images = []
        batch_conversations = []
        
        for sample in dataset:
            # Load image
            image = PILImage.open(sample['image']).convert('RGB')
            batch_images.append(image)
            batch_conversations.append(sample['conversations'])
        
        print(f"✅ Batch processing successful: {len(batch_images)} images, {len(batch_conversations)} conversations")
        
        # Memory usage check
        total_pixels = sum(img.width * img.height for img in batch_images)
        avg_conversation_length = sum(len(str(conv)) for conv in batch_conversations) / len(batch_conversations)
        
        print(f"📊 Batch stats:")
        print(f"  Total pixels: {total_pixels:,}")
        print(f"  Avg conversation length: {avg_conversation_length:.0f} chars")
        print(f"  Estimated memory per batch: ~{total_pixels * 3 / 1024**2:.1f} MB (images only)")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch loading failed: {e}")
        return False

def main():
    """Run all compatibility tests"""
    print("🔬 Gemma Dataset Compatibility Test Suite\n")
    
    results = {}
    
    # Test 1: Dataset loading
    dataset = test_dataset_loading()
    results['dataset_loading'] = dataset is not False
    
    if not dataset:
        print("\n❌ Cannot proceed without dataset")
        return results
    
    # Test 2: Image loading
    results['image_loading'] = test_image_loading(dataset)
    
    # Test 3: Chat format conversion
    converted_samples = test_gemma_chat_format_conversion(dataset)
    results['chat_conversion'] = len(converted_samples) > 0
    
    # Test 4: JSON output parsing
    results['json_parsing'] = test_json_output_parsing(dataset)
    
    # Test 5: Tokenization (optional)
    results['tokenization'] = test_tokenization_compatibility()
    
    # Test 6: Create training dataset
    training_dataset_path = create_training_ready_dataset(dataset)
    results['training_dataset'] = training_dataset_path is not None
    
    # Test 7: Small batch loading
    if training_dataset_path:
        results['batch_loading'] = test_small_batch_loading(training_dataset_path)
    else:
        results['batch_loading'] = False
    
    # Summary
    print("\n📋 Test Results Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests:.1%})")
    
    if passed_tests >= total_tests - 1:  # Allow tokenization to fail
        print("🎉 Dataset is ready for Gemma training!")
        
        next_steps = """
🚀 Next Steps:
1. Install required packages: pip install transformers datasets accelerate
2. Use training_data/pokemon_gemma_format.jsonl for training
3. Set up TRL SFTTrainer with Gemma model
4. Start with small learning rate (1e-5) and few epochs
"""
        print(next_steps)
    else:
        print("⚠️  Some issues detected. Review failed tests above.")
    
    return results

if __name__ == "__main__":
    main()