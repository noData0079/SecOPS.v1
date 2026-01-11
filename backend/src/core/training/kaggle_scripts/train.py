# train.py - Kaggle Script

import os
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset

# Configuration
max_seq_length = 2048
dtype = None # None for auto detection
load_in_4bit = True

def train():
    print("Starting Llama 3.3 Fine-tuning with Unsloth...")

    # 1. Load Model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/llama-3-8b-bnb-4bit", # Can be changed to Llama 3.3 when available/supported
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )

    # 2. Prepare Data
    # Assuming dataset is mounted at /kaggle/input/tsm99-it-distillation-data/
    data_files = {"train": "/kaggle/input/tsm99-it-distillation-data/training_data.jsonl"}
    dataset = load_dataset("json", data_files=data_files, split="train")

    def formatting_prompts_func(examples):
        scenarios = examples["scenario"]
        causes = examples["root_cause"]
        remediations = examples["remediation"]
        codes = examples["code_snippet"]
        texts = []
        for s, c, r, code in zip(scenarios, causes, remediations, codes):
            text = f"""### Scenario:
{s}

### Root Cause:
{c}

### Remediation:
{r}

### Code Snippet:
{code}
"""
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 3. Setup PEFT
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
    )

    # 4. Train
    from trl import SFTTrainer
    from transformers import TrainingArguments

    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        args = TrainingArguments(
            per_device_train_batch_size = 2,
            gradient_accumulation_steps = 4,
            warmup_steps = 5,
            max_steps = 60,
            learning_rate = 2e-4,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
        ),
    )

    trainer.train()

    # 5. Save/Export
    # In a real scenario, we would push to Hub or save to output for retrieval
    model.save_pretrained("lora_model")
    print("Training Complete. Model saved.")

if __name__ == "__main__":
    train()
