"""
ComfyUI Custom Nodes — Nano Banana 2 via VERTEX AI
Endpoint : aiplatform.googleapis.com
Docs : https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-generation

Différences vs AI Studio :
- Auth : Bearer token (pas de clé API)
- URL : projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}
- aspectRatio : champ valide dans generationConfig.imageConfig  ✅
"""

import os
import base64
import json
import io
import subprocess
import urllib.request
import urllib.error
import numpy as np
from PIL import Image
import torch


# ─────────────────────────────────────────────
#  Auth — Bearer token
# ─────────────────────────────────────────────

def _get_bearer_token(token_override: str = "") -> str:
    """
    Priorité :
    1. token_override (champ du noeud)
    2. Variable d'env GOOGLE_CLOUD_ACCESS_TOKEN
    3. `gcloud auth print-access-token` (si gcloud installé)
    """
    if token_override.strip():
        return token_override.strip()

    env_token = os.environ.get("GOOGLE_CLOUD_ACCESS_TOKEN", "").strip()
    if env_token:
        return env_token

    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    raise ValueError(
        "Impossible d'obtenir un Bearer token Vertex AI.\n"
        "Options :\n"
        "  1. Colle le token dans le champ 'access_token' du noeud\n"
        "  2. export GOOGLE_CLOUD_ACCESS_TOKEN=$(gcloud auth print-access-token)\n"
        "  3. Installe et configure gcloud CLI"
    )


# ─────────────────────────────────────────────
#  HTTP helpers
# ─────────────────────────────────────────────

def _build_url(project_id: str, location: str, model: str) -> str:
    # Location 'global' → endpoint global sans région dans le hostname
    if location == "global":
        base = "https://aiplatform.googleapis.com"
    else:
        base = f"https://{location}-aiplatform.googleapis.com"
    return (
        f"{base}/v1/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model}:generateContent"
    )


def _gemini_request(token: str, url: str, payload: dict, timeout: int = 300) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Vertex AI HTTP {e.code}: {body}") from e


def _extract_image(response: dict) -> str:
    candidates = response.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Pas de candidats dans la réponse : {response}")
    for part in candidates[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            return part["inlineData"]["data"]
    raise RuntimeError(
        "Aucune image dans la réponse Vertex AI.\n"
        f"Réponse brute : {response}"
    )


# ─────────────────────────────────────────────
#  Tensor helpers
# ─────────────────────────────────────────────

def _tensor_to_base64(tensor):
    arr = tensor[0].cpu().numpy()
    arr = (arr * 255).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/png"


def _base64_to_tensor(b64: str):
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


# ─────────────────────────────────────────────
#  Constantes
# ─────────────────────────────────────────────

# Aspect ratios supportés par Gemini 3.1 Flash Image sur Vertex
ASPECT_RATIOS = ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]

LOCATIONS = [
    "global",
    "us-central1",
    "us-east1",
    "us-west1",
    "europe-west1",
    "europe-west4",
    "asia-northeast1",
    "asia-southeast1",
]

# Modèles NB disponibles sur Vertex
MODELS = [
    "gemini-3.1-flash-image-preview",   # Nano Banana 2  (speed, volume)
    "gemini-3-pro-image-preview",        # Nano Banana Pro (qualité max)
]


# ─────────────────────────────────────────────
#  Node 1 — Text → Image
# ─────────────────────────────────────────────

class NanaBanana2TextToImage:
    CATEGORY = "NanaBanana2 / Vertex"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "A photorealistic portrait, soft studio lighting",
                }),
                "project_id": ("STRING", {
                    "default": os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
                    "tooltip": "Ton GCP Project ID",
                }),
                "location": (LOCATIONS, {"default": "us-central1"}),
                "model": (MODELS, {"default": "gemini-3.1-flash-image-preview"}),
                "aspect_ratio": (ASPECT_RATIOS, {"default": "1:1"}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "access_token": ("STRING", {
                    "default": "",
                    "tooltip": (
                        "Bearer token Vertex AI. Si vide :\n"
                        "1. GOOGLE_CLOUD_ACCESS_TOKEN env var\n"
                        "2. gcloud auth print-access-token"
                    ),
                }),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "use_search_grounding": ("BOOLEAN", {"default": False}),
            },
        }

    def generate(self, prompt, project_id, location, model, aspect_ratio,
                 negative_prompt="", access_token="", seed=-1,
                 use_search_grounding=False):

        if not project_id.strip():
            raise ValueError("project_id manquant.")

        token = _get_bearer_token(access_token)
        url = _build_url(project_id.strip(), location, model)

        full_prompt = prompt.strip()
        if negative_prompt.strip():
            full_prompt += f"\n\nDo NOT include: {negative_prompt.strip()}"

        # Sur Vertex, aspectRatio est un vrai champ dans imageConfig ✅
        generation_config = {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
            },
        }
        if seed != -1:
            generation_config["seed"] = seed

        payload = {
            "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": generation_config,
        }
        if use_search_grounding:
            payload["tools"] = [{"googleSearch": {}}]

        response = _gemini_request(token, url, payload)
        return (_base64_to_tensor(_extract_image(response)),)


# ─────────────────────────────────────────────
#  Node 2 — Image Edit (keep / change)
# ─────────────────────────────────────────────

class NanaBanana2ImageEdit:
    CATEGORY = "NanaBanana2 / Vertex"
    FUNCTION = "edit"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Keep the character / change the background to a beach at sunset",
                }),
                "project_id": ("STRING", {"default": os.environ.get("GOOGLE_CLOUD_PROJECT", "")}),
                "location": (LOCATIONS, {"default": "us-central1"}),
                "model": (MODELS, {"default": "gemini-3.1-flash-image-preview"}),
                "aspect_ratio": (ASPECT_RATIOS, {"default": "1:1"}),
            },
            "optional": {
                "access_token": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "use_search_grounding": ("BOOLEAN", {"default": False}),
            },
        }

    def edit(self, image, prompt, project_id, location, model, aspect_ratio,
             access_token="", seed=-1, use_search_grounding=False):

        if not project_id.strip():
            raise ValueError("project_id manquant.")

        token = _get_bearer_token(access_token)
        url = _build_url(project_id.strip(), location, model)
        b64_in, mime = _tensor_to_base64(image)

        generation_config = {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        }
        if seed != -1:
            generation_config["seed"] = seed

        payload = {
            "contents": [{"role": "user", "parts": [
                {"inlineData": {"mimeType": mime, "data": b64_in}},
                {"text": prompt.strip()},
            ]}],
            "generationConfig": generation_config,
        }
        if use_search_grounding:
            payload["tools"] = [{"googleSearch": {}}]

        response = _gemini_request(token, url, payload)
        return (_base64_to_tensor(_extract_image(response)),)


# ─────────────────────────────────────────────
#  Node 3 — Multi-Image Blend (jusqu'à 4 images)
# ─────────────────────────────────────────────

class NanaBanana2MultiImageBlend:
    CATEGORY = "NanaBanana2 / Vertex"
    FUNCTION = "blend"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_1": ("IMAGE",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Blend these references into a single cohesive scene",
                }),
                "project_id": ("STRING", {"default": os.environ.get("GOOGLE_CLOUD_PROJECT", "")}),
                "location": (LOCATIONS, {"default": "us-central1"}),
                "model": (MODELS, {"default": "gemini-3.1-flash-image-preview"}),
                "aspect_ratio": (ASPECT_RATIOS, {"default": "1:1"}),
            },
            "optional": {
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "access_token": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    def blend(self, image_1, prompt, project_id, location, model, aspect_ratio,
              image_2=None, image_3=None, image_4=None,
              access_token="", seed=-1):

        if not project_id.strip():
            raise ValueError("project_id manquant.")

        token = _get_bearer_token(access_token)
        url = _build_url(project_id.strip(), location, model)

        images = [img for img in (image_1, image_2, image_3, image_4) if img is not None]
        parts = []
        for img in images:
            b64, mime = _tensor_to_base64(img)
            parts.append({"inlineData": {"mimeType": mime, "data": b64}})
        parts.append({"text": prompt.strip()})

        generation_config = {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        }
        if seed != -1:
            generation_config["seed"] = seed

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": generation_config,
        }

        response = _gemini_request(token, url, payload)
        return (_base64_to_tensor(_extract_image(response)),)
