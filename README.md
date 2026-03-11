# 🍌 ComfyUI — Nano Banana 2 Nodes (Vertex AI)

Nœuds ComfyUI pour générer et éditer des images via **Nano Banana 2**  
via **Google Vertex AI** (`gemini-2.5-flash-image`).

---

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/TON_USERNAME/ComfyUI_NanaBanana2.git
```
Redémarre ComfyUI. Aucune dépendance pip requise.

---

## Auth — Bearer Token

Obtiens un token avec gcloud CLI :

```bash
gcloud auth login
gcloud auth print-access-token
```

**3 façons de le fournir (par priorité) :**

1. Champ `access_token` directement dans le noeud
2. Variable d'env :
   ```bash
   export GOOGLE_CLOUD_ACCESS_TOKEN=$(gcloud auth print-access-token)
   ```
3. gcloud installé → le noeud l'appelle automatiquement

> ⚠️ Le token expire après **1 heure**. Régénère-le avec `gcloud auth print-access-token`.

---

## Configuration requise

| Paramètre | Valeur |
|---|---|
| `project_id` | Ton GCP Project ID (ex: `t-pointer-473318-n7`) |
| `location` | `global` ← **obligatoire** pour ce modèle |
| `model` | `gemini-2.5-flash-image` |

---

## Nœuds disponibles

### 🍌 NB2 Text → Image
Génère une image depuis un prompt texte.

| Paramètre | Description |
|---|---|
| `prompt` | Description de l'image |
| `negative_prompt` | Ce à éviter |
| `aspect_ratio` | 1:1 / 16:9 / 9:16 / 3:4 / 4:3 / 21:9... |
| `seed` | -1 = aléatoire |
| `use_search_grounding` | Le modèle cherche sur Google pour plus de précision |

---

### 🍌 NB2 Image Edit (keep/change)
Édite une image existante. Format de prompt recommandé :

```
Keep the character and lighting / change the background to a neon cyberpunk street
```

---

### 🍌 NB2 Multi-Image Blend
Fusionne jusqu'à 4 images de référence + un prompt.

---

## Installer gcloud sur Lightning AI

```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
gcloud auth login --no-launch-browser
```
