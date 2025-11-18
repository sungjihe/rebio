# backend/tests/test_llm_load.py

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import os
from dotenv import load_dotenv
from pathlib import Path

# ==============================
# 1) 환경 변수 로드
# ==============================
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


# ==============================
# 2) GPU 체크
# ==============================
def detect_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


# ==============================
# 3) 모델 로드 함수
# ==============================
def load_biomistral_model(model_name="BioMistral/BioMistral-7B-Instruct"):
    device = detect_device()
    print(f"🚀 Device found: {device}")

    print(f"🔬 Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print(f"🧠 Loading BioMistral model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True,
        device_map=device
    )

    print("✅ Model loaded successfully!\n")
    return tokenizer, model, device


# ==============================
# 4) 질의 테스트 함수
# ==============================
def ask_model(tokenizer, model, device, query):
    print(f"📝 Query: {query}")

    inputs = tokenizer(query, return_tensors="pt").to(device)

    with torch.no_grad():
        start = time.time()
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            do_sample=True,
            top_p=0.92,
            temperature=0.6,
        )
        end = time.time()

    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\n💬 Response ({end - start:.2f}s):")
    print("---------------------------------------")
    print(answer)
    print("---------------------------------------\n")


# ==============================
# 5) Main
# ==============================
if __name__ == "__main__":
    print("\n============================================")
    print(" 🔬 BioMistral LLM GPU Load Test")
    print("============================================\n")

    tokenizer, model, device = load_biomistral_model(
        model_name="BioMistral/BioMistral-7B-Instruct"
    )

    # ❗ 원하는 테스트 질문 (추가해도 됨)
    test_queries = [
        "What diseases are associated with protein TP53?",
        "Suggest candidate drugs targeting EGFR mutation.",
        "Summarize the role of BRCA1 in DNA repair.",
        "Explain the relationship between IL6 and inflammatory response.",
        "What are typical inhibitors for JAK1 kinase?"
    ]

    for q in test_queries:
        ask_model(tokenizer, model, device, q)

    print("🎉 BioMistral GPU test completed!\n")
