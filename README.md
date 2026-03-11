# 🍌 ComfyUI — Nano Banana 2 Nodes

Nœuds ComfyUI pour générer et éditer des images via **Nano Banana 2**  
(Google Gemini 3.1 Flash Image Preview — `gemini-3.1-flash-image-preview`).

---

## Installation

1. Copie le dossier `ComfyUI_NanaBanana2` dans :
   ```
   ComfyUI/custom_nodes/ComfyUI_NanaBanana2/
   ```
2. Redémarre ComfyUI.
3. Aucune dépendance pip externe requise (utilise `urllib` + `Pillow` + `torch` déjà présents dans ComfyUI).

---

## Clé API

Obtiens ta clé sur [Google AI Studio](https://aistudio.google.com/apikey).

**2 façons de la fournir :**

- **Variable d'environnement (recommandé) :**
  ```bash
  export GEMINI_API_KEY="ta_clé"
  ```
- **Directement dans le nœud :** remplis le champ `api_key` (attention, la clé sera visible dans ton workflow JSON).

> ⚠️ Nano Banana 2 nécessite une clé API **payante** (pas de free tier pour ce modèle).

---

## Nœuds disponibles

### 🍌 NB2 Text → Image
Génère une image à partir d'un prompt texte.

| Paramètre | Description |
|---|---|
| `prompt` | Description de l'image souhaitée |
| `negative_prompt` | Ce à éviter (optionnel) |
| `aspect_ratio` | 1:1 / 16:9 / 9:16 / 3:4 / 4:3 / 21:9 / 4:1 / 1:8... (14 ratios) |
| `resolution` | 512 / 1024 / 2048 / 4096 |
| `seed` | -1 = aléatoire |
| `use_search_grounding` | Permet au modèle de chercher sur Google pour plus de précision |

---

### 🍌 NB2 Image Edit (keep/change)
Édite une image existante. Format de prompt recommandé (natif NB2) :

```
Keep the character and lighting / change the background to a neon cyberpunk street
```

| Paramètre | Description |
|---|---|
| `image` | Image source (tensor ComfyUI) |
| `prompt` | Instruction d'édition |
| `aspect_ratio` | Ratio de sortie |
| `resolution` | Résolution de sortie |

---

### 🍌 NB2 Multi-Image Blend
Fusionne jusqu'à 4 images de référence + un prompt.

| Paramètre | Description |
|---|---|
| `image_1..4` | Images de référence (image_1 obligatoire) |
| `prompt` | Instructions de fusion |

---

## Prix (API officielle Google — mars 2026)

| Résolution | Prix/image |
|---|---|
| 512 px (0.5K) | ~$0.019 |
| 1024 px (1K) | ~$0.067 |
| 2048 px (2K) | ~$0.099 |
| 4096 px (4K) | ~$0.151 |

Search grounding : gratuit pour les 5 000 premières requêtes/mois, puis $0.014/requête.

---

## Notes

- **1 image par requête** : c'est une limitation de l'API Gemini `generateContent` (pas de paramètre `n`).
- Toutes les images générées contiennent un watermark **SynthID** invisible.
- Timeout par défaut : 300 secondes (les générations 4K peuvent être lentes).
- Compatible avec l'**API APIYI** (proxy compatible Gemini, ~$0.03/req) — change simplement la base URL dans `nodes.py` si tu veux l'utiliser.
