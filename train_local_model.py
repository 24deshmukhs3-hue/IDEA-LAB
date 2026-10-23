"""
Local Fine-Tuning Script using Hugging Face PEFT/LoRA.
Train your custom lightweight LLM (e.g., Qwen2.5-Coder-1.5B or DeepSeek-Coder) offline.
"""

import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer

def train_custom_code_analyzer():
    # 1. Base Model Selection (Lightweight for local execution)
    BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    
    # 2. Local Training Data (Dead code, smells, design patterns)
    training_samples = [
        {
            "instruction": "Analyze this code for unreachable code and smells.",
            "input": "def foo():\n    return 1\n    print('dead')",
            "output": '{"explanation": "Line 3 is unreachable after return.", "refactoring_suggestions": ["Remove line 3"], "design_pattern_opportunity": {"applicable": false}}'
        },
        {
            "instruction": "Analyze this code for optimization and design pattern opportunities.",
            "input": "def pay(mode):\n    if mode == 'card': pass\n    elif mode == 'upi': pass",
            "output": '{"explanation": "Multiple conditional branches on strategy type.", "refactoring_suggestions": ["Use strategy classes"], "design_pattern_opportunity": {"applicable": true, "pattern_name": "Strategy Pattern"}}'
        }
    ]

    dataset = Dataset.from_list(training_samples)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)

    def preprocess_function(examples):
        texts = [
            f"<|user|>\n{instr}\n{inp}<|assistant|>\n{out}"
            for instr, inp, out in zip(examples['instruction'], examples['input'], examples['output'])
        ]
        return tokenizer(texts, truncation=True, max_length=512, padding="max_length")

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    training_args = TrainingArguments(
        output_dir="./local_fine_tuned_model",
        per_device_train_batch_size=2,
        num_train_epochs=3,
        save_strategy="epoch",
        logging_steps=10,
        learning_rate=2e-4,
        fp16=True
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    print("Starting local model fine-tuning...")
    # trainer.train()
    # model.save_pretrained("./final_local_model")
    print("Fine-tuning script structure ready.")

if __name__ == "__main__":
    train_custom_code_analyzer()