# backend/agentic/nodes/vision_node.py

import os
import json
import logging
from typing import Dict, Any

import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from openai import OpenAI

from backend.agentic.state import HeliconState
from backend.agentic.utils.biomistral import BioMistralReasoner

logger = logging.getLogger("VisionNode")
logging.basicConfig(level=logging.INFO)


class VisionNode:
    """
    ***Hybrid Vision Node***
    BLIP2 → GPT-4o Vision → BioMistral reasoning

    1) BLIP2: coarse caption (초기 baseline 정보)
    2) GPT-4o: 고정밀 이미지 분석 및 엔티티/관계 추출
    3) BioMistral: 생물학적 interpretation (mutation / function / disease)
    """

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # ========== BLIP2 로드시작 ==========
        logger.info(f"[VisionNode] Loading BLIP2 captioner on {device} ...")
        self.processor = Blip2Processor.from_pretrained(
            "Salesforce/blip2-flan-t5-xl"
        )
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-flan-t5-xl",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        ).to(device)

        # ========== GPT-4o 준비 ==========
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # ========== BioMistral Reasoner 로드 ==========
        self.reasoner = BioMistralReasoner()

    # ---------------------------------------------------
    # GPT-4o Vision 분석
    # ---------------------------------------------------
    def _analyze_with_gpt4o(self, image_b64: str, question: str) -> Dict[str, Any]:
        system = (
            "You are a biomedical vision expert. "
            "Analyze the image carefully and extract biological entities such as proteins, "
            "genes, domains, structural features, interactions, disease associations, "
            "and experimental context. Produce structured data."
        )

        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_b64}},
                    ],
                },
            ],
            temperature=0.2,
            max_tokens=900
        )

        return response.choices[0].message.content

    # ---------------------------------------------------
    # run()
    # ---------------------------------------------------
    def run(self, state: HeliconState) -> HeliconState:

        image_path = state.entities.get("image_path")
        if not image_path or not os.path.exists(image_path):
            logger.warning("[VisionNode] No valid image path provided.")
            state.image_evidence = None
            return state

        logger.info(f"[VisionNode] Processing image: {image_path}")
        image = Image.open(image_path).convert("RGB")

        # ======================================================================
        # 1) BLIP2 기준 캡션
        # ======================================================================
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            caption_ids = self.model.generate(**inputs, max_new_tokens=100)
            blip_caption = self.processor.tokenizer.decode(
                caption_ids[0], skip_special_tokens=True
            )
        logger.info(f"[VisionNode] BLIP2 caption: {blip_caption}")

        # ======================================================================
        # 2) GPT-4o Vision로 고정밀 이미지 이해
        # ======================================================================
        from base64 import b64encode
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        b64 = b64encode(buf.getvalue()).decode("utf-8")
        image_b64 = f"data:image/png;base64,{b64}"

        # GPT-4o Vision 질문 prompt
        user_question = state.entities.get("question", "Analyze this image.")

        gpt4o_raw = self._analyze_with_gpt4o(image_b64, user_question)
        logger.info("[VisionNode] GPT-4o visual analysis complete.")

        # ======================================================================
        # 3) BioMistral로 생물학적 해석
        # ======================================================================
        prompt = f"""
You are a biomedical scientist.

Image caption (BLIP2):
{blip_caption}

GPT-4o Vision extraction:
{gpt4o_raw}

Provide structured biological interpretation:
- proteins or domains visible
- structural features
- mutation/function insights
- assay context
- disease relevance
Return JSON only.
"""

        biomistral_out = self.reasoner.generate(prompt)

        try:
            evidence = json.loads(biomistral_out)
        except Exception:
            evidence = {
                "blip_caption": blip_caption,
                "gpt4o_result": gpt4o_raw,
                "interpretation": biomistral_out,
            }

        state.image_evidence = evidence
        state.log("vision_node", evidence)

        return state
