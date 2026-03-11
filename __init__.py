"""
ComfyUI Custom Node — Nano Banana 2 (Gemini 3.1 Flash Image)
Installation : copie ce dossier dans ComfyUI/custom_nodes/
"""

from .nodes import (
    NanaBanana2TextToImage,
    NanaBanana2ImageEdit,
    NanaBanana2MultiImageBlend,
)

NODE_CLASS_MAPPINGS = {
    "NanaBanana2TextToImage":     NanaBanana2TextToImage,
    "NanaBanana2ImageEdit":       NanaBanana2ImageEdit,
    "NanaBanana2MultiImageBlend": NanaBanana2MultiImageBlend,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NanaBanana2TextToImage":     "🍌 NB2 Text → Image",
    "NanaBanana2ImageEdit":       "🍌 NB2 Image Edit (keep/change)",
    "NanaBanana2MultiImageBlend": "🍌 NB2 Multi-Image Blend",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
