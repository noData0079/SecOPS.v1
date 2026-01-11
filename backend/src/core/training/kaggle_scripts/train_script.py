import os
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Configuration - "Vertical IT" Focused
model_name = "unsloth/Llama-3.3-70B-Instruct-bnb-4bit" # Or 8B for faster local testing
max_seq_length = 2048
load_in_4bit = True

# 2. Load Model & Tokenizer (Fast Patching)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    load_in_4bit = load_in_4bit,
)

# 3. Add LoRA Adapters (The "Self-Evolution" Layer)
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
)

# 4. Prepare DeepSeek-Generated Dataset
# This loads the sanitized 'IT-only' data your platform created
dataset = load_dataset("json", data_files="training_data.jsonl", split="train")

# 5. Initialize the Trainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # Adjust based on dataset size
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        output_dir = "tsm99_evolved_weights",
    ),
)

# 6. Execute One-Click Training
trainer.train()

# 7. Export for Local Sovereignty (Ollama/GGUF)
model.save_pretrained_gguf("tsm99_model_v1", tokenizer, quantization_method = "q4_k_m")
