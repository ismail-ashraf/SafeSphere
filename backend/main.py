import os
import re
import zipfile
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Any

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoTokenizer

try:
    import shap
except Exception:
    shap = None

from models.nlp_model import MasterSequentialModel, predict_shap_backend
from models.violence_model import build_violence_model

BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = BASE_DIR / ".runtime_models"
RUNTIME_DIR.mkdir(exist_ok=True)

# 1) Load normal .env first.
load_dotenv(BASE_DIR / ".env", override=True)

# 2) Support the old team file format:
#    os.environ["NAME"] = r"C:\\path\\file"
# This keeps your old models_path.env style working without needing manual conversion.
def _load_legacy_models_path_file() -> None:
    for filename in ["models_path.env", "models_path.env.example"]:
        path = BASE_DIR / filename
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(errors="ignore")
        pattern = r'os\.environ\["(?P<key>[A-Z0-9_]+)"\]\s*=\s*r?["\'](?P<value>.*?)["\']'
        for match in re.finditer(pattern, content):
            value = match.group("value").strip()
            # Ignore placeholders from the original example file.
            if value and " path" not in value.lower():
                os.environ[match.group("key")] = value

_load_legacy_models_path_file()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SafeSphere-Core")

TOXICITY_MODEL_PATH = os.getenv("TOXICITY_MODEL_PATH")
VIOLENCE_MODEL_PATH = os.getenv("VIOLENCE_MODEL_PATH")
TOXICITY_TOKENIZER_DIR = os.getenv("TOXICITY_TOKENIZER_DIR", "distilbert-base-uncased")
TOXICITY_BASE_MODEL_DIR = os.getenv("TOXICITY_BASE_MODEL_DIR", os.getenv("TOXICITY_TOKENIZER_DIR", "distilbert-base-uncased"))
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
ENABLE_SHAP = os.getenv("ENABLE_SHAP", "false").lower() in {"1", "true", "yes", "on"}
MODEL_LOAD_STRICT = os.getenv("MODEL_LOAD_STRICT", "false").lower() in {"1", "true", "yes", "on"}
IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", "224"))
TEXT_MAX_LENGTH = int(os.getenv("TEXT_MAX_LENGTH", "128"))
TOXIC_THRESHOLD = float(os.getenv("TOXIC_THRESHOLD", "0.70"))
VIOLENCE_THRESHOLD = float(os.getenv("VIOLENCE_THRESHOLD", "0.70"))
REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", "0.50"))


def _path_string(path_value: Optional[str]) -> Optional[str]:
    if path_value is None:
        return None
    value = path_value.strip().strip('"').strip("'")
    if not value:
        return None
    return os.path.expandvars(os.path.expanduser(value))


def _absolute_path(path_value: str) -> Path:
    path = Path(_path_string(path_value) or "")
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def _find_first_file(root: Path, suffixes: tuple[str, ...]) -> Optional[Path]:
    for suffix in suffixes:
        matches = list(root.rglob(f"*{suffix}"))
        if matches:
            return matches[0]
    return None


def _find_tokenizer_dir(root: Path) -> Path:
    marker_files = {"tokenizer.json", "tokenizer_config.json", "vocab.txt", "special_tokens_map.json"}
    candidates = [root] + [p for p in root.rglob("*") if p.is_dir()]
    for folder in candidates:
        names = {p.name for p in folder.iterdir() if p.is_file()}
        if names.intersection(marker_files):
            return folder
    # Fallback: if zip contains a single folder, use it.
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if len(dirs) == 1:
        return dirs[0]
    return root


def _extract_zip(zip_path: Path, asset_name: str) -> Path:
    target = RUNTIME_DIR / asset_name
    stamp = target / ".extracted"
    if not stamp.exists():
        if target.exists():
            # keep simple and safe; do not delete user files outside runtime.
            pass
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target)
        stamp.write_text(str(time.time()), encoding="utf-8")
    return target


def _prepare_model_file(path_value: Optional[str], name: str, suffixes: tuple[str, ...]) -> Path:
    if not path_value:
        raise RuntimeError(f"{name} is empty. Set it in backend/.env or backend/models_path.env")
    path = _absolute_path(path_value)
    if not path.exists():
        raise FileNotFoundError(f"{name} does not exist: {path}")

    # Some Windows setups show PyTorch .pt/.pth files as compressed zip archives.
    # Also sometimes the file is literally named model.pt.zip. A PyTorch model file
    # can still be loaded directly by torch.load even if Windows says it is a zip.
    # So: if the filename contains .pt/.pth/.h5/.weights.h5, keep it as-is first.
    lower_name = path.name.lower()
    if path.is_file() and (path.suffix.lower() in suffixes or any(s in lower_name for s in suffixes)):
        return path

    # Only extract a real generic .zip when the filename does NOT already look like
    # a model file. This is useful for tokenizer zips or zips that contain a model file.
    if path.is_file() and path.suffix.lower() == ".zip":
        extracted = _extract_zip(path, f"{name.lower()}_zip")
        found = _find_first_file(extracted, suffixes)
        if found:
            return found
        raise FileNotFoundError(f"{name} zip extracted, but no model file {suffixes} found inside: {path}")

    raise RuntimeError(f"{name} must point to a model file {suffixes} or a .zip containing it. Got: {path}")


def _prepare_tokenizer_path(path_value: Optional[str]) -> str:
    if not path_value:
        return "distilbert-base-uncased"
    raw = _path_string(path_value)
    path = Path(raw or "")

    # Hugging Face model id, not a local path.
    if raw and not path.is_absolute() and not (BASE_DIR / path).exists():
        return raw

    local = _absolute_path(raw or "")
    if not local.exists():
        raise FileNotFoundError(f"TOXICITY_TOKENIZER_DIR does not exist: {local}")
    if local.is_file() and local.suffix.lower() == ".zip":
        extracted = _extract_zip(local, "tokenizer_zip")
        return str(_find_tokenizer_dir(extracted))
    if local.is_dir():
        return str(_find_tokenizer_dir(local))
    raise RuntimeError(f"TOXICITY_TOKENIZER_DIR must be a folder, Hugging Face model id, or .zip. Got: {local}")


def _risk_level(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.50:
        return "Medium"
    return "Low"


def _decision_from_scores(image_score: Optional[float], text_score: Optional[float]) -> dict:
    reasons = []
    needs_review = False
    rejected = False

    if image_score is not None:
        if image_score >= VIOLENCE_THRESHOLD:
            rejected = True
            reasons.append("Violence detected in image")
        elif image_score >= REVIEW_THRESHOLD:
            needs_review = True
            reasons.append("Image needs manual review")

    if text_score is not None:
        if text_score >= TOXIC_THRESHOLD:
            rejected = True
            reasons.append("Toxic language detected in text")
        elif text_score >= REVIEW_THRESHOLD:
            needs_review = True
            reasons.append("Text needs manual review")

    max_score = max([score for score in [image_score, text_score] if score is not None], default=0)

    if rejected:
        final_decision = "Rejected"
        recommended_action = "Block content"
    elif needs_review:
        final_decision = "Needs Review"
        recommended_action = "Send to manual review"
    else:
        final_decision = "Approved"
        recommended_action = "Allow content"
        reasons = ["No unsafe content detected"]

    return {
        "final_decision": final_decision,
        "risk_level": _risk_level(max_score),
        "reason": ", ".join(reasons),
        "recommended_action": recommended_action,
    }


class TextPayload(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


def _load_text_model(device: torch.device):
    tokenizer_path = _prepare_tokenizer_path(TOXICITY_TOKENIZER_DIR)
    model_path = _prepare_model_file(TOXICITY_MODEL_PATH, "TOXICITY_MODEL_PATH", (".pt", ".pth"))

    logger.info("[STARTUP] Loading tokenizer from: %s", tokenizer_path)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    logger.info("[STARTUP] Loading text model from: %s", model_path)
    try:
        loaded: Any = torch.load(model_path, map_location=device, weights_only=False)
    except TypeError:
        loaded = torch.load(model_path, map_location=device)

    # Case 1: full model saved with torch.save(model, path)
    if isinstance(loaded, nn.Module):
        model = loaded.to(device)
        model.eval()
        return tokenizer, model

    # Case 2: checkpoint dict / state_dict
    if isinstance(loaded, dict):
        state_dict = loaded.get("model_state_dict") or loaded.get("state_dict") or loaded
        base_path = _prepare_tokenizer_path(TOXICITY_BASE_MODEL_DIR)
        logger.info("[STARTUP] Loading text base model from: %s", base_path)
        model = MasterSequentialModel(base_path).to(device)
        model.load_state_dict(state_dict, strict=False)
        model.eval()
        return tokenizer, model

    raise RuntimeError("Unsupported toxicity model file. Expected nn.Module or state_dict checkpoint.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[STARTUP] Loading SafeSphere AI models...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    app.state.device = device
    app.state.enable_shap = ENABLE_SHAP and shap is not None

    app.state.nlp_ready = False
    app.state.nlp_error = None
    app.state.image_ready = False
    app.state.image_error = None

    try:
        app.state.tokenizer, app.state.nlp_model = _load_text_model(device)
        app.state.nlp_ready = True

        if app.state.enable_shap:
            logger.info("[STARTUP] Initializing SHAP explainer...")
            app.state.explainer = shap.Explainer(
                lambda x: predict_shap_backend(x, app.state.nlp_model, app.state.tokenizer, app.state.device),
                app.state.tokenizer,
            )
        else:
            app.state.explainer = None
            logger.info("[STARTUP] SHAP disabled")
    except Exception as exc:
        app.state.nlp_error = str(exc)
        logger.exception("Text model failed to load")
        if MODEL_LOAD_STRICT:
            raise

    try:
        violence_path = _absolute_path(VIOLENCE_MODEL_PATH or "") if VIOLENCE_MODEL_PATH else None
        if not violence_path or not violence_path.exists():
            raise FileNotFoundError(f"VIOLENCE_MODEL_PATH does not exist: {violence_path}")
        if violence_path.suffix.lower() in {".ipynb", ".py"}:
            raise RuntimeError(
                "VIOLENCE_MODEL_PATH points to code/notebook, not trained weights. "
                "Use a .h5/.weights.h5 file exported from the notebook."
            )
        violence_model_file = _prepare_model_file(str(violence_path), "VIOLENCE_MODEL_PATH", (".h5", ".keras"))
        logger.info("[STARTUP] Loading violence model from: %s", violence_model_file)
        app.state.violence_model = build_violence_model(str(violence_model_file))
        app.state.image_classes = ["Non_Violence", "Violence"]
        app.state.image_ready = True
    except Exception as exc:
        app.state.image_error = str(exc)
        logger.exception("Image model failed to load")
        if MODEL_LOAD_STRICT:
            raise

    logger.info(
        "[STARTUP] SafeSphere API started. text_ready=%s image_ready=%s",
        app.state.nlp_ready,
        app.state.image_ready,
    )

    yield

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="SafeSphere AI Moderation API",
    description="Text toxicity and image violence moderation API.",
    version="3.1.0-no-docker-custom-paths",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Monitoring"])
def root():
    return {"service": "SafeSphere API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["Monitoring"])
def health_check():
    return {
        "status": "healthy" if getattr(app.state, "nlp_ready", False) and getattr(app.state, "image_ready", False) else "degraded",
        "text_model_ready": getattr(app.state, "nlp_ready", False),
        "text_model_error": getattr(app.state, "nlp_error", None),
        "image_model_ready": getattr(app.state, "image_ready", False),
        "image_model_error": getattr(app.state, "image_error", None),
        "shap_enabled": bool(getattr(app.state, "enable_shap", False)),
        "device": str(getattr(app.state, "device", "unknown")),
        "paths": {
            "TOXICITY_MODEL_PATH": TOXICITY_MODEL_PATH,
            "TOXICITY_TOKENIZER_DIR": TOXICITY_TOKENIZER_DIR,
            "TOXICITY_BASE_MODEL_DIR": TOXICITY_BASE_MODEL_DIR,
            "VIOLENCE_MODEL_PATH": VIOLENCE_MODEL_PATH,
        },
    }


def _require_text_model_loaded():
    if not getattr(app.state, "nlp_ready", False):
        raise HTTPException(status_code=503, detail=f"Text model is not loaded: {getattr(app.state, 'nlp_error', 'unknown error')}")


def _require_image_model_loaded():
    if not getattr(app.state, "image_ready", False):
        raise HTTPException(status_code=503, detail=f"Image model is not loaded: {getattr(app.state, 'image_error', 'unknown error')}")


def analyze_text_internal(text: str) -> dict:
    _require_text_model_loaded()
    start_time = time.time()
    tokenizer = app.state.tokenizer
    model = app.state.nlp_model
    device = app.state.device

    inputs = tokenizer(
        text,
        max_length=TEXT_MAX_LENGTH,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        output = model(inputs["input_ids"], inputs["attention_mask"])
        logits = output.logits if hasattr(output, "logits") else output
        probabilities = F.softmax(logits, dim=1)

    toxic_score = float(probabilities[0][1].item())
    is_toxic = toxic_score >= TOXIC_THRESHOLD
    highlighted_text = text

    if app.state.enable_shap and app.state.explainer is not None:
        shap_values = app.state.explainer([text])
        tokens = shap_values.data[0]
        values = shap_values.values[0, :, 1]

        output_html = []
        for token, val in zip(tokens, values):
            if token in ["[CLS]", "[SEP]", "[PAD]"] or not str(token).strip():
                continue
            safe_token = str(token).replace("<", "&lt;").replace(">", "&gt;")
            if val >= 0.07:
                intensity = min(int(val * 255 * 2.0), 255)
                output_html.append(
                    f"<span class='ai-highlight-token' style='color: rgb({intensity}, 0, 0); font-weight: 700; background-color: #ffe6e6; padding: 0 2px; border-radius: 4px;'>{safe_token}</span>"
                )
            else:
                output_html.append(safe_token)
        highlighted_text = " ".join(output_html).replace(" ##", "")

    return {
        "original_text": text,
        "is_toxic": is_toxic,
        "toxic_confidence_percentage": round(toxic_score * 100, 2),
        "toxic_score": round(toxic_score, 4),
        "clean_score": round(1 - toxic_score, 4),
        "risk_level": _risk_level(toxic_score),
        "highlighted_html_text": highlighted_text,
        "processing_time_ms": round((time.time() - start_time) * 1000, 2),
    }


def analyze_image_internal(contents: bytes) -> dict:
    _require_image_model_loaded()
    start_time = time.time()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Failed to read image file.")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (IMAGE_SIZE, IMAGE_SIZE))
    img_array = np.expand_dims(img_resized, axis=0).astype("float32")

    predictions = app.state.violence_model.predict(img_array)
    class_index = int(np.argmax(predictions[0]))
    confidence = float(predictions[0][class_index])
    violence_score = float(predictions[0][1])

    return {
        "status": "success",
        "prediction": app.state.image_classes[class_index],
        "confidence": f"{confidence * 100:.2f}%",
        "confidence_percentage": round(confidence * 100, 2),
        "violence_score": round(violence_score, 4),
        "safe_score": round(1 - violence_score, 4),
        "is_violence": violence_score >= VIOLENCE_THRESHOLD,
        "risk_level": _risk_level(violence_score),
        "processing_time_ms": round((time.time() - start_time) * 1000, 2),
    }


@app.post("/predict/text", tags=["Inference"])
async def analyze_text(payload: TextPayload):
    try:
        return analyze_text_internal(payload.text)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Text inference error")
        raise HTTPException(status_code=500, detail=f"Text processing error: {str(e)}")


@app.post("/predict/image", tags=["Inference"])
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    try:
        contents = await file.read()
        return analyze_image_internal(contents)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image inference error")
        raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")


@app.post("/predict/combined", tags=["Inference"])
async def analyze_combined(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    if not text and file is None:
        raise HTTPException(status_code=400, detail="Provide text, image, or both.")

    try:
        text_result = analyze_text_internal(text) if text else None
        image_result = None

        if file is not None:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
            image_result = analyze_image_internal(await file.read())

        decision = _decision_from_scores(
            image_result["violence_score"] if image_result else None,
            text_result["toxic_score"] if text_result else None,
        )

        return {
            **decision,
            "image_result": image_result,
            "text_result": text_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Combined inference error")
        raise HTTPException(status_code=500, detail=f"Combined processing error: {str(e)}")
