import os
from dataclasses import dataclass
from typing import Dict, List, Any

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "rebio_lora_training.jsonl")

# ⚠️ 실제 HF 모델 이름으로 교체 필요
BASE_MODEL_NAME = "BioMistral/BioMistral-7B"  # <- 여기 수정해서 사용


# ==========================================
# 1) 데이터셋 로드
# ==========================================
def load_rebio_dataset():
    ds = load_dataset(
        "json",
        data_files={"train": DATA_PATH},
    )
    return ds["train"]


# ==========================================
# 2) 프롬프트 템플릿 정의
# ==========================================
def build_prompt(example: Dict[str, Any]) -> str:
    task = example.get("task", "general")
    inst = example.get("instruction", "")
    inp = example.get("input", "")

    prompt = (
        f"[TASK] {task}\n\n"
        f"[INSTRUCTION]\n{inst}\n\n"
        f"[INPUT]\n{inp}\n\n"
        f"[ANSWER]\n"
    )
    return prompt


# ==========================================
# 3) Tokenization
# ==========================================
def tokenize_fn(example, tokenizer, max_length=2048):
    prompt = build_prompt(example)
    output = example["output"]

    full_text = prompt + output

    tokenized = tokenizer(
        full_text,
        truncation=True,
        max_length=max_length,
        padding="max_length",
    )

    # labels = input_ids 그대로 (언어모델 방식 학습)
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized


# ==========================================
# 4) DataCollator (단순 버전)
# ==========================================
@dataclass
class DataCollatorForCausalLM:
    tokenizer: Any
    max_length: int = 2048

    def __call__(self, batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        ids = [b["input_ids"] for b in batch]
        attn = [b["attention_mask"] for b in batch]
        labels = [b["labels"] for b in batch]

        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(attn, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def main():
    # ======================================
    # 모델/토크나이저 로드
    # ======================================
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # ======================================
    # LoRA 설정
    # ======================================
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ======================================
    # 데이터 전처리
    # ======================================
    train_ds_raw = load_rebio_dataset()
    train_ds = train_ds_raw.map(
        lambda ex: tokenize_fn(ex, tokenizer),
        remove_columns=train_ds_raw.column_names,
    )

    collator = DataCollatorForCausalLM(tokenizer=tokenizer)

    # ======================================
    # 학습 설정
    # ======================================
    output_dir = os.path.join(BASE_DIR, "models", "rebio_biomistral_lora")

    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=20,
        save_steps=200,
        save_total_limit=3,
        warmup_ratio=0.03,
        weight_decay=0.01,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        data_collator=collator,
    )

    trainer.train()

    # LoRA weight 저장
    model.save_pretrained(output_dir)
    print(f"[INFO] LoRA weights saved to: {output_dir}")


if __name__ == "__main__":
    main()
