"""
Multi-provider OCR and vision extraction pipeline for educational images.
"""

import os
import logging
import base64
from typing import Dict, Optional
from PIL import Image

logger = logging.getLogger(__name__)


class VisionExtractor:
    """
    Orchestrates OCR and Vision extraction using PaddleOCR, TrOCR, Groq Vision, and Gemini Vision.
    Lazily loads deep learning models (Paddle/TrOCR) to save RAM if not needed.
    """
    
    def __init__(self):
        self.paddle_ocr = None
        self.trocr_processor = None
        self.trocr_model = None

    def _init_paddle(self):
        if self.paddle_ocr is None:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

    def _init_trocr(self):
        if self.trocr_processor is None:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            self.trocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
            self.trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

    def _call_groq_vision(self, image_path: str, prompt: str) -> str:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-90b-vision-preview",
        )
        return chat_completion.choices[0].message.content

    def _call_gemini_vision(self, image_path: str, prompt: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        sample_file = Image.open(image_path)
        response = model.generate_content([prompt, sample_file])
        return response.text

    def extract(self, image_path: str, content_hint: Optional[str] = "auto") -> Dict[str, str]:
        """
        Extracts content from images using the multi-provider fallback.
        1. PaddleOCR (Printed)
        2. TrOCR (Handwritten)
        3. Groq Vision (Diagrams)
        4. Gemini Vision (Fallback)
        """
        logger.info(f"[Vision] Processing '{image_path}' (hint: {content_hint})")
        
        if content_hint == "auto":
            try:
                self._init_paddle()
                result = self.paddle_ocr.ocr(image_path, cls=True)
                
                if not result or not result[0]:
                    content_hint = "diagram" 
                else:
                    confidences = [word_info[1][1] for word_info in result[0]]
                    avg_conf = sum(confidences) / len(confidences) if confidences else 0
                    
                    if avg_conf < 0.6:
                        content_hint = "handwritten"
                    else:
                        content_hint = "printed"
            except Exception as e:
                logger.warning(f"[Vision] Auto-detection failed: {e}. Defaulting to 'diagram'.")
                content_hint = "diagram"
                
        result_text = ""
        method_used = ""
        
        if content_hint == "printed":
            self._init_paddle()
            res = self.paddle_ocr.ocr(image_path, cls=True)
            if res and res[0]:
                result_text = "\n".join([line[1][0] for line in res[0]])
            method_used = "PaddleOCR"
             
        elif content_hint == "handwritten":
            self._init_trocr()
            image = Image.open(image_path).convert("RGB")
            pixel_values = self.trocr_processor(images=image, return_tensors="pt").pixel_values
            generated_ids = self.trocr_model.generate(pixel_values)
            result_text = self.trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            method_used = "TrOCR"
             
        elif content_hint == "diagram":
            prompt = "Please extract all readable text and comprehensively describe any diagrams, charts, graphs, or visual elements in this educational image."
            try:
                result_text = self._call_groq_vision(image_path, prompt)
                method_used = "Groq_Vision"
            except Exception as e:
                logger.warning(f"[Vision] Groq Vision failed ({e}), falling back to Gemini Vision")
                result_text = self._call_gemini_vision(image_path, prompt)
                method_used = "Gemini_Vision"
                 
        return {"text": result_text, "method_used": method_used}
