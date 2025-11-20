# backend/agentic/nodes/vision_node.py

...
class VisionNode:
    """
    VisionNode — TherapeuticProtein version
    BLIP2 → GPT-4o Vision → BioMistral reasoning
    """

    ...

    def run(self, state: HeliconState) -> HeliconState:

        image_path = state.entities.get("image_path")
        if not image_path or not os.path.exists(image_path):
            logger.warning("[VisionNode] No valid image path.")
            state.vision_data = None
            return state

        logger.info(f"[VisionNode] Processing image: {image_path}")
        image = Image.open(image_path).convert("RGB")

        # ================================
        # 1) BLIP2 caption
        # ================================
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            caption_ids = self.model.generate(**inputs, max_new_tokens=100)
            blip_caption = self.processor.tokenizer.decode(
                caption_ids[0], skip_special_tokens=True
            )

        # ================================
        # 2) GPT-4o Vision
        # ================================
        import io
        from base64 import b64encode

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_b64 = "data:image/png;base64," + b64encode(buf.getvalue()).decode()

        question = state.entities.get("question", "Analyze this image.")
        gpt4o_raw = self._analyze_with_gpt4o(image_b64, question)

        # ================================
        # 3) BioMistral interpretation
        # ================================
        prompt = f"""
Image caption (BLIP2):
{blip_caption}

GPT-4o Vision output:
{gpt4o_raw}

Return structured biological interpretation (JSON).
"""

        biom = self.reasoner.generate(prompt)

        try:
            evidence = json.loads(biom)
        except:
            evidence = {
                "caption": blip_caption,
                "gpt4o": gpt4o_raw,
                "interpretation": biom,
            }

        # Unified output
        state.vision_data = evidence
        state.log("vision_node", evidence)

        return state
