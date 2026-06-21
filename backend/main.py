import os
import logging
import time
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shap

# استيراد معمارية الموديلات من المجلد الفرعي models
from models.nlp_model import MasterSequentialModel, predict_shap_backend
from models.violence_model import build_violence_model

# 1. إعداد الـ Logging لمراقبة السيرفر
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SafeSphere-Core")

# 2. قراءة ملف المسارات وتشغيله لحقن متغيرات البيئة
try:
    with open("models_path.env", "r", encoding="utf-8") as f:
        exec(f.read())
    logger.info("✅ Successfully loaded environmental paths from models_path.env")
except Exception as e:
    logger.error(f"⚠️ Could not read from models_path.env: {str(e)}")

# سحب المسارات المحقونة من الـ os.environ
TOXICITY_MODEL_PATH = os.environ.get("TOXICITY_MODEL_PATH")
VIOLENCE_MODEL_PATH = os.environ.get("VIOLENCE_MODEL_PATH")
TOXICITY_TOKENIZER_DIR = os.environ.get("TOXICITY_TOKENIZER_DIR")


# 3. إدارة دورة حياة التطبيق (Lifespan) لتحميل الموديلات والـ Explainer في الذاكرة
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[STARTUP] Loading both AI models into system memory...")
    
    # 🚨 التحقق الأمني من وجود المسارات أولاً لمنع الـ Crash الشهير
    if not TOXICITY_MODEL_PATH or not VIOLENCE_MODEL_PATH or not TOXICITY_TOKENIZER_DIR:
        critical_err = (
            f"🚨 خطأ فادح: أحد المسارات فارغ في ملف models_path.env!\n"
            f"TOXICITY_MODEL_PATH: {TOXICITY_MODEL_PATH}\n"
            f"VIOLENCE_MODEL_PATH: {VIOLENCE_MODEL_PATH}\n"
            f"TOXICITY_TOKENIZER_DIR: {TOXICITY_TOKENIZER_DIR}"
        )
        logger.critical(critical_err)
        raise RuntimeError(critical_err)

    if not os.path.exists(TOXICITY_MODEL_PATH) or not os.path.exists(VIOLENCE_MODEL_PATH) or not os.path.exists(TOXICITY_TOKENIZER_DIR):
        critical_err = (
            f"🚨 خطأ: ملفات الموديلات أو مجلد التوكينايزر مش موجودة في المسارات المحددة فعلياً على الجهاز!\n"
            f"يرجى مراجعة المسارات في ملف models_path.env"
        )
        logger.critical(critical_err)
        raise FileNotFoundError(critical_err)
        
    try:
        # --- أ) إعداد موديل الـ NLP (PyTorch) ---
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        app.state.device = device
        
        # تحميل التوكينايزر من الفولدر المحلي المكتوب في الـ env
        from transformers import AutoTokenizer
        logger.info(f"[STARTUP] Loading Tokenizer from local directory: {TOXICITY_TOKENIZER_DIR}")
        app.state.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        
        # بناء وتحميل أوزان موديل النصوص
        nlp_model = MasterSequentialModel().to(device)
        nlp_model.load_state_dict(torch.load(TOXICITY_MODEL_PATH, map_location=device))
        nlp_model.eval()
        app.state.nlp_model = nlp_model
        
        # بناء الـ SHAP Explainer وتثبيته في الذاكرة لسرعة الاستجابة
        logger.info("[STARTUP] Initializing SHAP Text Explainer backend...")
        app.state.explainer = shap.Explainer(
            lambda x: predict_shap_backend(x, app.state.nlp_model, app.state.tokenizer, app.state.device), 
            app.state.tokenizer
        )
        
        # --- ب) إعداد موديل الصور (TensorFlow) ---
        logger.info(f"[STARTUP] Loading Violence model from local file: {VIOLENCE_MODEL_PATH}")
        app.state.violence_model = build_violence_model(VIOLENCE_MODEL_PATH)
        app.state.image_classes = ["Non_Violence", "Violence"]
        
        logger.info("🎉 [SUCCESS] All Systems Operational. SafeSphere API is Live!")
        
    except Exception as e:
        logger.error(f"Failed to initialize application models: {str(e)}")
        raise e
        
    yield
    # تنظيف الـ GPU Cache عند إغلاق السيرفر
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# 4. إنشاء التطبيق وربطه بالـ Lifespan
app = FastAPI(
    title="SafeSphere Multi-Modal Aggregator API", 
    description="Backend API providing synchronized text toxicity analysis (PyTorch + SHAP XAI) and video/image violence detection (TensorFlow).",
    version="2.0.0", 
    lifespan=lifespan
)

# 5. إعداد الـ CORS لضمان استقبال الطلبات من الـ UI بدون مشاكل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 6. الـ Pydantic Schemas للتحقق من المدخلات والمخرجات
class TextPayload(BaseModel):
    text: str

# 7. الـ Endpoints (نقاط الاتصال)

@app.get("/health", tags=["Monitoring"])
def health_check():
    return {
        "status": "healthy", 
        "pipeline_ready": hasattr(app.state, "nlp_model") and hasattr(app.state, "violence_model")
    }


@app.post("/predict/text", tags=["Inference"])
async def analyze_text(payload: TextPayload):
    start_time = time.time()
    try:
        tokenizer = app.state.tokenizer
        model = app.state.nlp_model
        device = app.state.device
        
        # حساب التصنيف ونسبة الثقة للجملة ككل
        inputs = tokenizer(payload.text, max_length=128, padding="max_length", truncation=True, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(inputs['input_ids'], inputs['attention_mask'])
            probabilities = F.softmax(logits, dim=1)
            
        toxic_score = probabilities[0][1].item()
        is_toxic = bool(torch.argmax(probabilities, dim=1).item() == 1)
        
        # تشغيل خوارزمية الـ SHAP لاستخراج قيم تأثير الكلمات
        shap_values = app.state.explainer([payload.text])
        tokens = shap_values.data[0]
        values = shap_values.values[0, :, 1]
        
        # صياغة النص بـ HTML Tags ملونة ومجهزة للفرونت إند مباشرة
        output_html = []
        for token, val in zip(tokens, values):
            if token in ['[CLS]', '[SEP]', '[PAD]'] or not token.strip(): 
                continue
            if val >= 0.07:
                intensity = min(int(val * 255 * 2.0), 255)
                output_html.append(f"<span style='color: rgb({intensity}, 0, 0); font-weight: bold; background-color: #ffe6e6; padding: 0 2px;'>{token}</span>")
            else:
                output_html.append(token)

        highlighted_text = " ".join(output_html).replace(" ##", "")
        
        return {
            "original_text": payload.text,
            "is_toxic": is_toxic,
            "toxic_confidence_percentage": round(toxic_score * 100, 2),
            "highlighted_html_text": highlighted_text,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Text Inference Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"حدث خطأ في معالجة النص: {str(e)}")


@app.post("/predict/image", tags=["Inference"])
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="الملف المرفوع ليس صورة صالحة.")
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="فشل في قراءة ملف الصورة.")
        
        # التجهيز المسبق (Preprocessing) المتوافق مع تدريب الموديل
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (224, 224))
        img_array = np.expand_dims(img_resized, axis=0).astype('float32')
        
        # التوقع عبر موديل الـ TensorFlow
        predictions = app.state.violence_model.predict(img_array)
        class_index = np.argmax(predictions[0])
        confidence = float(predictions[0][class_index])
        
        return {
            "status": "success",
            "prediction": app.state.image_classes[class_index],
            "confidence": f"{confidence * 100:.2f}%"
        }
    except Exception as e:
        logger.error(f"Image Inference Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"حدث خطأ في معالجة الصورة: {str(e)}")