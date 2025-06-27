
A Comprehensive Guide to Dataset Preparation for Fine-Tuning Mistral's Pixtral Model


Section 1: Foundational Concepts: The Architectural Underpinnings of Pixtral's Data Requirements

To effectively fine-tune Mistral's Pixtral model, a comprehensive understanding of its underlying architecture is essential. The specific data format required for fine-tuning is not an arbitrary convention; rather, it is a direct consequence of the model's sophisticated design, which is optimized for processing interleaved sequences of text and images. This section deconstructs the key architectural components of Pixtral and explains how they dictate the structure of the training data.

1.1. Dissecting the Pixtral Architecture

Pixtral is a state-of-the-art vision-language model (VLM) that demonstrates strong performance on both multimodal and text-only benchmarks.1 Its architecture is a carefully engineered fusion of two primary components: a novel Vision Encoder and a powerful Multimodal Transformer Decoder.4
Multimodal Transformer Decoder: The text-processing core of Pixtral is a 12-billion-parameter decoder based on the Mistral Nemo architecture.4 This foundation ensures that Pixtral retains top-tier language understanding and generation capabilities, a design choice that prevents the degradation of text performance often seen when adding vision capabilities to language models.2
Vision Encoder (Pixtral-ViT): The image-processing component is a 400-million-parameter Vision Transformer (Pixtral-ViT) trained from scratch by Mistral AI.1 This custom encoder is specifically designed to handle images of variable sizes and aspect ratios natively, a key differentiator from models that require images to be resized to a fixed resolution.6
Architectural Integration: The vision encoder and the language decoder are linked by a fully connected network (often referred to as a projection layer).9 This network transforms the visual embeddings produced by Pixtral-ViT into the same dimensional space as the text embeddings, allowing them to be seamlessly integrated and processed by the language decoder.9 The model is then pre-trained on vast datasets of natively interleaved image and text data, teaching it to reason across both modalities within a single, continuous sequence.5
This two-part design allows Pixtral to leverage a powerful, pre-existing language model while integrating a highly specialized vision component, forming the basis for its robust multimodal reasoning skills.

1.2. The Image Tokenization Process: From Pixels to Semantics

A critical innovation in Pixtral's architecture is how it converts an image into a sequence of tokens that the language decoder can understand. This process is fundamental to its ability to handle variable image resolutions and preserve spatial information.5
The process involves several steps:
Patching: The input image is divided into a grid of non-overlapping square patches, each 16x16 pixels in size.5
Tokenization: Each 16x16 patch is converted into a single "image token" or embedding.5
Spatial Encoding with Special Tokens: To help the model understand the two-dimensional layout of the image, two types of special tokens are inserted into the sequence:
``: This token is inserted after each complete row of image patches (except for the final row). It acts as a carriage return, signaling to the model the end of a horizontal line of visual information.5
``: This token is appended at the very end of the sequence for a given image, signifying the completion of all visual data for that image.5
For example, processing a 512x512 pixel image would result in a sequence of 1,056 tokens consumed within the model's context window 5:
A grid of 32×32 patches (512/16=32), resulting in 32×32=1024 image tokens.
31 `` tokens (one for each of the first 31 rows).
1 `` token.
This tokenization strategy is what allows Pixtral to ingest images at their "natural resolution and aspect ratio," as the number of tokens simply scales with the image dimensions, preserving the original spatial relationships between different parts of the image.5

1.3. Implications for Data Formatting: Why Interleaving Matters

The architectural design and pre-training methodology of Pixtral directly dictate the optimal format for fine-tuning data. Since the model is trained to predict the next text token based on a sequence of interleaved image and text data, fine-tuning datasets must replicate this structure to be effective.5
A simple dataset of isolated (image, caption) pairs is insufficient because it does not teach the model how to handle images that are embedded within a conversational or instructional context. The model's strength lies in its ability to process a prompt that might start with text, present an image, and then continue with more text, all within a single user turn. Therefore, the fine-tuning data must be structured as a conversational exchange where images are treated as first-class components of the user's input, interleaved with text as needed for the specific task. This approach ensures that the fine-tuning process aligns with the model's native processing capabilities, leading to better performance on complex, real-world multimodal tasks.

Section 2: The Official Mistral AI Fine-Tuning Data Format for Pixtral

When fine-tuning Pixtral using the official Mistral AI platform and API, adherence to a specific data format is mandatory. This format is an extension of the one used for text-only models, adapted to accommodate multimodal inputs. While the documentation for text fine-tuning is explicit, the multimodal format requires synthesizing information from the vision API and platform behavior.

2.1. File Format: JSON Lines (.jsonl)

All data for fine-tuning, for both training and validation sets, must be provided in the JSON Lines file format, which has a .jsonl extension.12 In this format, each line in the file is a complete, self-contained JSON object representing a single data sample. This structure allows for efficient streaming and processing of large datasets.

2.2. The Core JSON Structure: The messages Array

Each JSON object on a line within the .jsonl file must contain a single top-level key: "messages".12 The value associated with this key is a list (or array) of dictionaries. Each dictionary in the list represents a single turn in a conversation.
Each turn dictionary must contain the following keys:
"role": A string indicating the author of the message. This can be "user", "assistant", or "system".12
"content": The content of the message. The structure of this field is what distinguishes text-only from multimodal data.
Crucially, the model's training loss is computed only on the tokens corresponding to messages with "role": "assistant".12 This means the model learns to generate responses that match the assistant's content, based on the preceding user and system messages.

2.3. The Multimodal content Structure for Pixtral

This is the most critical aspect of formatting data for Pixtral. While for text-only models the "content" field is a simple string, for multimodal user messages, the "content" field must be a list of dictionaries.5 This allows for the interleaving of text and images.
Each dictionary within this content list represents a distinct part of the user's message and must have a "type" key to specify its nature.
For a text segment: The dictionary should be {"type": "text", "text": "Your prompt text goes here."}.11
For an image: The dictionary should be {"type": "image_url", "image_url": {"url": "..."}}.11
This structure allows for flexible and complex prompts. A user can provide introductory text, then an image, followed by a concluding question, all within a single "user" turn by adding corresponding dictionaries to the content list in the desired order.

2.4. Image Representation and Encoding

The "url" field within the image_url object can be specified in two ways, providing flexibility for different data hosting scenarios.
Method 1: Publicly Accessible URL: You can provide a standard http:// or https:// link to an image file. The Mistral AI platform will download and process the image from this URL during the fine-tuning job.14 This method is convenient for datasets where images are already hosted online.
Method 2: Base64 Encoded Data URI: For local files, private images, or to create a fully self-contained dataset, images must be encoded in Base64. The resulting string is then embedded in a data URI. The format for the "url" value must be precise: "data:[MIME_type];base64,[base64_encoded_string]".11 For a JPEG image, this would look like
"data:image/jpeg;base64,...". This is the most robust and recommended method as it eliminates external dependencies and ensures the data's integrity and availability.

2.5. A Concrete .jsonl Example for Pixtral Fine-Tuning

The following is a complete, single-line example from a .jsonl file, demonstrating the correct format for a one-turn conversation involving both text and a Base64-encoded image. This example aims to fine-tune the model to generate product descriptions from an image.

JSON


{"messages":}, {"role": "assistant", "content": "Discover the epitome of craftsmanship with our Artisan's Choice Leather Backpack. Meticulously crafted from full-grain, vegetable-tanned leather, this backpack combines timeless style with rugged durability. Its spacious main compartment, padded laptop sleeve, and multiple organizational pockets make it the perfect companion for both urban commutes and weekend adventures. The solid brass hardware and rich, hand-finished patina ensure it only gets better with age."}]}


In this example:
The entire structure is a single JSON object on one line.
The "messages" key contains a list with two turns: one from the "user" and one from the "assistant".
The user's "content" is a list containing two parts: a text prompt and an image, correctly formatted with a Base64 data URI.
The assistant's "content" is the target completion that the model will learn to generate.

Table 1: Detailed Breakdown of the Pixtral .jsonl Data Structure

To provide a clear and unambiguous reference, the table below details every component of the required JSON structure for fine-tuning Pixtral.

Key
Parent Key
Data Type
Required?
Description
messages
Root Object
List of Dictionaries
Yes
The main container for the conversational exchange. Each item in the list is a single turn.
role
messages item
String
Yes
Specifies the author of the turn. Must be one of "user", "assistant", or "system".
content
messages item
String or List of Dictionaries
Yes
Contains the message content. For text-only turns, this is a string. For multimodal user turns, this must be a list of dictionaries.
type
content item (if list)
String
Yes
Specifies the type of content part. Must be "text" or "image_url".
text
content item (if list)
String
Conditional
Required if type is "text". Contains the text segment of the prompt.
image_url
content item (if list)
Dictionary
Conditional
Required if type is "image_url". Contains the image information.
url
image_url
String
Yes
The URL of the image. Can be a public http(s):// link or a Base64 data URI (data:image/...;base64,...).


Section 3: Practical Implementation: A Step-by-Step Guide to Creating and Launching a Fine-Tuning Job

With a clear understanding of the data format, the next step is to implement a workflow to prepare the data and launch a fine-tuning job using the Mistral AI API. This section provides a practical, step-by-step guide, including a complete Python script for data preparation.

3.1. Data Curation and Preparation

The success of any fine-tuning task is overwhelmingly dependent on the quality of the training data.16 Before writing any code, it is crucial to:
Define a Clear Use Case: Determine the specific task the model should learn. Examples include generating product descriptions from images, answering questions about charts and graphs, or describing scenes in a particular style.18
Gather High-Quality Data: Collect a dataset of high-quality image-text pairs that are directly relevant to your use case. The data should be clean, accurate, and diverse enough to cover the expected range of inputs.
Create Training and Validation Sets: It is essential to split your curated data into at least two files: a training set and a validation set.12 The training set is used to update the model's weights, while the validation set, which the model does not train on, is used to periodically evaluate the model's performance on unseen data. This process is critical for monitoring progress and detecting overfitting.17 A typical split might be 80-90% of the data for training and 10-20% for validation.

3.2. Data Processing Workflow: From Raw Data to .jsonl

The following Python script provides a complete workflow for converting a raw dataset into the required .jsonl format for Pixtral fine-tuning. This script assumes you have a CSV file (dataset.csv) with three columns: image_path (the local path to the image file), prompt (the user's text instruction), and completion (the desired assistant response). It also assumes all images are in a subdirectory named images/.

Python


import pandas as pd
import base64
import json
import os
from PIL import Image
from io import BytesIO

def get_image_mime_type(image_path):
    """Determines the MIME type of an image based on its extension."""
    ext = os.path.splitext(image_path).lower()
    if ext == ".jpg" or ext == ".jpeg":
        return "image/jpeg"
    elif ext == ".png":
        return "image/png"
    elif ext == ".webp":
        return "image/webp"
    else:
        # Default or raise an error for unsupported types
        return "application/octet-stream"

def encode_image_to_base64(image_path):
    """Reads an image file and encodes it to a Base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None

def create_jsonl_from_csv(csv_path, output_path):
    """
    Reads a CSV, processes each row to create a multimodal JSON object,
    and writes it to a.jsonl file.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return

    with open(output_path, 'w') as f:
        for index, row in df.iterrows():
            image_path = row['image_path']
            prompt_text = row['prompt']
            completion_text = row['completion']

            # Encode the image
            base64_image = encode_image_to_base64(image_path)
            if base64_image is None:
                continue # Skip if image encoding failed

            # Get MIME type and construct the data URI
            mime_type = get_image_mime_type(image_path)
            data_uri = f"data:{mime_type};base64,{base64_image}"

            # Construct the JSON object in the required format
            json_object = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": data_uri}}
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": completion_text
                    }
                ]
            }

            # Write the JSON object as a new line in the.jsonl file
            f.write(json.dumps(json_object) + "\n")

    print(f"Successfully created {output_path}")

# --- Main Execution ---
if __name__ == "__main__":
    # Assuming you have split your data into training and validation CSVs
    create_jsonl_from_csv('training_data.csv', 'training.jsonl')
    create_jsonl_from_csv('validation_data.csv', 'validation.jsonl')



This script automates the most error-prone part of the process: correctly encoding images and structuring the JSON object.

3.3. The Fine-Tuning Process via Mistral's API

Once the training.jsonl and validation.jsonl files are prepared, you can use the mistralai Python client to manage the fine-tuning job.
Step 1: Install the Client and Set Up API Key
First, install the library and ensure your API key is available as an environment variable.

Bash


pip install mistralai
export MISTRAL_API_KEY="YOUR_API_KEY"


Step 2: Upload Data Files
The prepared .jsonl files must be uploaded to the Mistral platform.

Python


from mistralai.client import MistralClient

client = MistralClient() # Assumes MISTRAL_API_KEY is set in environment

# Upload the training data file
with open("training.jsonl", "rb") as f:
    training_data = client.files.create(file=("training.jsonl", f), purpose="fine-tune")
print(f"Training file uploaded with ID: {training_data.id}")

# Upload the validation data file
with open("validation.jsonl", "rb") as f:
    validation_data = client.files.create(file=("validation.jsonl", f), purpose="fine-tune")
print(f"Validation file uploaded with ID: {validation_data.id}")


The purpose parameter must be set to "fine-tune".12 The API will return a unique file ID for each uploaded file.
Step 3: Create the Fine-Tuning Job
Using the file IDs, create the fine-tuning job.

Python


from mistralai.models.jobs import TrainingParameters

created_job = client.fine_tuning.jobs.create(
    model="pixtral-12b-2409",  # Specify the Pixtral model
    training_files=[training_data.id],
    validation_files=[validation_data.id],
    hyperparameters=TrainingParameters(
        training_steps=100,  # Number of training steps
        learning_rate=1.0e-5 # Learning rate
    )
)
print(f"Fine-tuning job created with ID: {created_job.id}")


Here, you specify the model to fine-tune, provide the file IDs, and set hyperparameters like training_steps and learning_rate.12
Step 4: Monitor the Job and Retrieve the Fine-Tuned Model
You can programmatically check the status of your job.

Python


import time

job_id = created_job.id
while True:
    retrieved_job = client.fine_tuning.jobs.get(job_id)
    status = retrieved_job.status
    print(f"Job Status: {status}")
    if status in:
        break
    time.sleep(60)

if retrieved_job.status == "SUCCESS":
    fine_tuned_model_id = retrieved_job.fine_tuned_model
    print(f"Fine-tuning successful! Model ID: {fine_tuned_model_id}")
else:
    print(f"Fine-tuning job finished with status: {retrieved_job.status}")


Once the job status is "SUCCESS", the retrieved_job object will contain the ID of your new, fine-tuned model, which can then be used for inference via the chat completions API.12

Section 4: Alternative Fine-Tuning Ecosystems and Format Considerations

While the official Mistral AI API provides a managed, straightforward path for fine-tuning, many developers and researchers prefer the flexibility and control offered by open-source ecosystems, primarily centered around Hugging Face. However, choosing this path introduces different data formatting considerations and, most importantly, a critical model format discrepancy that can impact deployment.

4.1. The Hugging Face Ecosystem (trl, peft)

The most common open-source approach for fine-tuning VLMs like Pixtral involves a combination of Hugging Face libraries:
transformers: Provides the core model and processor classes.18
datasets: For loading and manipulating datasets.18
peft (Parameter-Efficient Fine-Tuning): Implements methods like LoRA (Low-Rank Adaptation), which drastically reduce the computational resources required for fine-tuning by only training a small number of adapter weights instead of the entire model.20
trl (Transformer Reinforcement Learning Library): Offers high-level abstractions like the SFTTrainer (Supervised Fine-tuning Trainer) that simplify the training loop.18
In this ecosystem, the data formatting is handled differently. Instead of manually creating the JSON structure, the developer typically defines a chat template. The AutoProcessor, which bundles the model's tokenizer and image processor, uses a method called apply_chat_template.16 This function takes a conversational dictionary (similar in concept to the
messages array) and automatically formats it into the correct input sequence for the model, inserting the special [IMG] placeholders and handling all tokenization internally.24 This abstracts away the complexity of manual formatting.

4.2. Critical Insight: The Model Format Discrepancy

A significant challenge arises from the fact that there are two different "formats" for the Pixtral model in the wild:
The "Native" Mistral Format: This is the format used by Mistral's own tools and inference backends like vLLM. It is often referred to as the "consolidated" format.25
The Hugging Face transformers Format: To integrate Pixtral into the existing transformers library, it was adapted to fit the LlavaForConditionalGeneration architecture, a common structure for VLMs in the ecosystem.24
This divergence has a profound implication: LoRA adapters trained on the Hugging Face version of Pixtral are not directly compatible with inference servers that expect the native Mistral format.25 A developer who fine-tunes a model using
trl and peft will produce adapter weights for the transformers model structure. If they then try to deploy this model using an optimized inference server like vLLM that only supports the native format, the process will fail.
Fortunately, the community has developed workarounds. Conversion scripts are available that can take a model fine-tuned in the Hugging Face ecosystem (with merged LoRA adapters) and transform its architecture and weights back into the vLLM-compatible native Mistral format.25 This is a crucial, non-obvious step that must be factored into any production pipeline that uses open-source tooling for training and high-performance servers for inference.

4.3. High-Performance Frameworks: Unsloth and Axolotl

For users seeking maximum performance and efficiency, specialized fine-tuning frameworks like Unsloth and Axolotl have emerged. These tools are built on top of libraries like PyTorch and PEFT but include significant optimizations to accelerate training speed and reduce GPU memory usage.28
Unsloth: Known for delivering 2-5x faster training speeds and up to 80% less VRAM usage compared to standard methods. It achieves this through custom CUDA kernels and memory management techniques.28
Axolotl: A highly configurable framework that supports a wide range of models and fine-tuning techniques, including DeepSpeed ZeRO for distributed training.29
These frameworks often support Pixtral and provide their own configuration files (e.g., YAML) to define the dataset path and training parameters, further abstracting the data loading process.30 While they offer superior performance, they still operate within the Hugging Face ecosystem, meaning the model format discrepancy remains a relevant consideration for deployment.

Table 2: Comparison of Pixtral Fine-Tuning Platforms

The choice of platform is a strategic decision with trade-offs. The following table compares the primary approaches.
Feature
Mistral AI API
Hugging Face (trl/peft)
Advanced Frameworks (Unsloth/Axolotl)
Ease of Use
High: Fully managed service. No GPU management needed.
Medium: Requires Python scripting and environment setup.
Medium-Low: Requires configuration via YAML files and understanding of advanced concepts.
Data Format
Strict: Manual .jsonl creation with Base64 encoding required.
Flexible: apply_chat_template handles most formatting automatically.
Flexible: Manages data loading based on config files.
Control
Low: Limited hyperparameter tuning (training_steps, learning_rate).
High: Full control over training loop, optimizers, schedulers, and LoRA config.
High: Extensive configuration options for performance and training strategy.
Cost
Usage-based: Pay-per-job pricing, no upfront hardware cost.32
Hardware-dependent: Requires renting or owning powerful GPUs.
Hardware-dependent: Requires GPU resources, but optimizes their use.
Performance
Standard: Performance is determined by Mistral's backend.
Standard: Baseline performance of open-source libraries.
Very High: Significantly faster training and lower memory usage.29
Deployment
Seamless: Produces a model ID directly usable in Mistral's ecosystem.
Complex: Produces HF-format adapters that may require conversion for deployment.25
Complex: Same as Hugging Face; requires model format conversion for non-HF backends.


Section 5: Expert Recommendations: Best Practices and Common Pitfalls

Fine-tuning a sophisticated vision-language model like Pixtral is a nuanced process. Success depends not only on correct data formatting but also on adhering to established best practices and avoiding common errors. This section synthesizes expert recommendations to guide users toward achieving optimal results.

5.1. Dataset Quality is Paramount

The single most influential factor in a successful fine-tuning project is the quality of the dataset. The principle of "garbage in, garbage out" is magnified in the context of fine-tuning.14
High-Quality Examples: Ensure that every example in your dataset is accurate, clean, and directly representative of the task you want the model to perform. A smaller, high-quality dataset is vastly superior to a large, noisy one.16
Task Alignment: The data must be tailored to your specific goal, whether it's adopting a certain tone, generating responses in a specific JSON format, or answering domain-specific questions.19
Diversity: The dataset should be diverse enough to prevent the model from overfitting to a narrow set of examples, which would impair its ability to generalize to new, unseen inputs.17

5.2. A Robust Validation Strategy

A validation set is not an optional component; it is an indispensable tool for assessing model performance and health.17
Holdout Data: The validation set must consist of data that the model has not been trained on. These examples should be of the same quality and format as the training data.21
Monitoring Overfitting: During training, periodically calculate the loss on the validation set. If the training loss continues to decrease while the validation loss begins to stagnate or increase, it is a clear sign of overfitting. At this point, training should be stopped (a technique known as early stopping) to prevent the model from memorizing the training data and losing its generalization ability.17
Platform Support: Both the Mistral AI API and open-source trainers like SFTTrainer explicitly support the use of a validation dataset to provide these crucial metrics during the training process.12

5.3. Hyperparameter Starting Points

While optimal hyperparameters are dataset-dependent, there are well-established starting points for fine-tuning a 12B-parameter VLM like Pixtral.
Learning Rate: A low learning rate is crucial to avoid destabilizing the pre-trained weights. A value around 1e-5 to 3e-5 is a common and effective starting point.34
Batch Size: Vision-language models are extremely memory-intensive. It is often necessary to use a very small per-device batch size, such as 1 or 2, especially when training on a single GPU (e.g., an NVIDIA A40 or A100).34 To simulate a larger effective batch size without increasing memory, use gradient accumulation.
Epochs: Full fine-tuning on a specialized task often requires only a few passes over the dataset. Training for 2 to 4 epochs is typically sufficient to adapt the model without causing catastrophic forgetting of its original capabilities.16

5.4. Common Pitfalls and Troubleshooting

GPU Memory Exhaustion: This is the most frequent issue. To mitigate it, use Parameter-Efficient Fine-Tuning (PEFT) methods like QLoRA, which involves loading the model in 4-bit precision. Additionally, enable gradient checkpointing and use the smallest possible batch size.20 Frameworks like Unsloth are specifically designed to minimize memory usage.29
Data Format Validation Errors: The Mistral API validates .jsonl files upon upload. A single syntax error in one JSON object can cause the entire file validation to fail. Meticulously check for valid JSON syntax, correct key names, and the proper multimodal content structure before uploading to save time and avoid unnecessary costs.12
Model Evaluation Sensitivity: As noted in the original Pixtral paper, model performance can be highly sensitive to the exact phrasing of prompts and the strictness of evaluation metrics.2 When testing your fine-tuned model, evaluate it on a variety of prompts. Do not rely solely on exact-match accuracy; consider semantic correctness as well. For example, a model responding with "6" instead of "6.0" is substantively correct but would fail an exact-match test.2
Model Format Incompatibility: As detailed in Section 4.2, be aware of the difference between the native Mistral model format and the Hugging Face transformers format. Plan your deployment strategy before you begin fine-tuning to avoid discovering that your trained artifacts are incompatible with your target inference server.25
Works cited
Pixtral-12B-2409 is now available on Amazon Bedrock Marketplace - AWS, accessed June 21, 2025, https://aws.amazon.com/blogs/machine-learning/pixtral-12b-2409-is-now-available-on-amazon-bedrock-marketplace/
Pixtral 12B - arXiv, accessed June 21, 2025, https://arxiv.org/html/2410.07073v2
(PDF) Pixtral 12B - ResearchGate, accessed June 21, 2025, https://www.researchgate.net/publication/384770053_Pixtral_12B
Pixtral 12B: A Guide With Practical Examples - DataCamp, accessed June 21, 2025, https://www.datacamp.com/tutorial/pixtral-12b
mistral-on-aws/notebooks/Pixtral-samples/Pixtral_capabilities.ipynb at main - GitHub, accessed June 21, 2025, https://github.com/aws-samples/mistral-on-aws/blob/main/notebooks/Pixtral-samples/Pixtral_capabilities.ipynb
Announcing Pixtral 12B - Mistral AI, accessed June 21, 2025, https://mistral.ai/news/pixtral-12b
Pixtral 12B - Paper Details - ChatPaper - AI, accessed June 21, 2025, https://www.chatpaper.ai/dashboard/paper/64fbc922-b6ed-47b7-9934-3eb49f0eea88
[Literature Review] Pixtral 12B - Moonlight | AI Colleague for Research Papers, accessed June 21, 2025, https://www.themoonlight.io/en/review/pixtral-12b
Pixtral 12B — Another great multimodal model - UnfoldAI, accessed June 21, 2025, https://unfoldai.com/pixtral-12b/
Pixtral Large Explained - Encord, accessed June 21, 2025, https://encord.com/blog/pixtral-large-explained/
Vision | Mistral AI, accessed June 21, 2025, https://docs.mistral.ai/capabilities/vision/
Text Fine-tuning | Mistral AI Large Language Models, accessed June 21, 2025, https://docs.mistral.ai/capabilities/finetuning/text_finetuning/
mistral-on-aws/Deployment/SageMaker/Pixtral-12b-LMI-SageMaker ..., accessed June 21, 2025, https://github.com/aws-samples/mistral-on-aws/blob/main/Deployment/SageMaker/Pixtral-12b-LMI-SageMaker-realtime-inference.ipynb
Pixtral 12b 240910 · Models - Dataloop, accessed June 21, 2025, https://dataloop.ai/library/model/mistral-community_pixtral-12b-240910/
Pixtral Large: A Guide With Examples - DataCamp, accessed June 21, 2025, https://www.datacamp.com/tutorial/pixtral-large
Repository with minimal code to fine tune Pixtral on your own data. - GitHub, accessed June 21, 2025, https://github.com/AlexandrosChrtn/pixtral-finetune
6 Common LLM Fine-Tuning Mistakes Everyone Should Know - MonsterAPI, accessed June 21, 2025, https://blog.monsterapi.ai/common-llm-fine-tuning-mistakes/
How to Fine-Tune Multimodal Models or VLMs with Hugging Face TRL - Philschmid, accessed June 21, 2025, https://www.philschmid.de/fine-tune-multimodal-llms-with-trl
Fine-tuning - Mistral AI Documentation, accessed June 21, 2025, https://docs.mistral.ai/guides/finetuning/
Fine-Tune Mistral-7B with LoRA A Quickstart Guide - DigitalOcean, accessed June 21, 2025, https://www.digitalocean.com/community/tutorials/mistral-7b-fine-tuning
Understanding Validation file and Fine tuning file - API - OpenAI Developer Community, accessed June 21, 2025, https://community.openai.com/t/understanding-validation-file-and-fine-tuning-file/515662
Mistral Fine-Tuning: The Basics and a Quick Tutorial - Kolena, accessed June 21, 2025, https://www.kolena.com/guides/mistral-fine-tuning-the-basics-and-a-quick-tutorial/
Fine-tuning Mistral on Your Dataset - Hugging Face, accessed June 21, 2025, https://huggingface.co/blog/nroggendorff/finetune-mistral
Pixtral - Hugging Face, accessed June 21, 2025, https://huggingface.co/docs/transformers/main/model_doc/pixtral
[New Model][Format]: Support the HF-version of Pixtral · Issue #8685 · vllm-project/vllm, accessed June 21, 2025, https://github.com/vllm-project/vllm/issues/8685
mistral-community/pixtral-12b · Any leads on how to fine-tune Pixtral on custom dataset for reference? - Hugging Face, accessed June 21, 2025, https://huggingface.co/mistral-community/pixtral-12b/discussions/12
[Feature]: LoRA support for Pixtral · Issue #8802 · vllm-project/vllm - GitHub, accessed June 21, 2025, https://github.com/vllm-project/vllm/issues/8802
unsloth/Pixtral-12B-2409 - Hugging Face, accessed June 21, 2025, https://huggingface.co/unsloth/Pixtral-12B-2409
Comparing Fine Tuning Frameworks - Hyperbolic, accessed June 21, 2025, https://hyperbolic.xyz/blog/comparing-finetuning-frameworks
Building a Production Multimodal Fine-Tuning Pipeline | Google Cloud Blog, accessed June 21, 2025, https://cloud.google.com/blog/topics/developers-practitioners/building-a-production-multimodal-fine-tuning-pipeline
Vision-language tuning - Anyscale Docs, accessed June 21, 2025, https://docs.anyscale.com/llms/finetuning/guides/tasks/vision_language_tuning/
Fine-tuning Overview - Mistral AI Documentation, accessed June 21, 2025, https://docs.mistral.ai/capabilities/finetuning/finetuning_overview/
Why might my fine-tuned Sentence Transformer perform worse on a task than the original pre-trained model did? - Milvus, accessed June 21, 2025, https://milvus.io/ai-quick-reference/why-might-my-finetuned-sentence-transformer-perform-worse-on-a-task-than-the-original-pretrained-model-did
Fine tuning Pixtral - Multi-modal Vision and Text Model - YouTube, accessed June 21, 2025, https://www.youtube.com/watch?v=1N76mJ1pMro
A Step-by-Step Guide to Fine-Tuning the Mistral 7B LLM - E2E Networks, accessed June 21, 2025, https://www.e2enetworks.com/blog/a-step-by-step-guide-to-fine-tuning-the-mistral-7b-llm
Best practices for finetuning LLMs : r/LocalLLaMA - Reddit, accessed June 21, 2025, https://www.reddit.com/r/LocalLLaMA/comments/1gr2kag/best_practices_for_finetuning_llms/


