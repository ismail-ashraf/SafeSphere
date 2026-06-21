# SafeSphere API Contract

Base URL locally:

```txt
http://localhost:8000
```

---

## Health Check

```txt
GET /health
```

Response:

```json
{
  "status": "healthy",
  "pipeline_ready": true,
  "shap_enabled": false,
  "device": "cpu"
}
```

---

## Text Moderation

```txt
POST /predict/text
Content-Type: application/json
```

Request:

```json
{
  "text": "sample user generated text"
}
```

Response:

```json
{
  "original_text": "sample user generated text",
  "is_toxic": false,
  "toxic_confidence_percentage": 8.25,
  "toxic_score": 0.0825,
  "clean_score": 0.9175,
  "risk_level": "Low",
  "highlighted_html_text": "sample user generated text",
  "processing_time_ms": 42.31
}
```

---

## Image Moderation

```txt
POST /predict/image
Content-Type: multipart/form-data
```

Form field:

```txt
file: image file
```

Response:

```json
{
  "status": "success",
  "prediction": "Violence",
  "confidence": "91.20%",
  "confidence_percentage": 91.2,
  "violence_score": 0.912,
  "safe_score": 0.088,
  "is_violence": true,
  "risk_level": "High",
  "processing_time_ms": 118.5
}
```

---

## Combined Moderation

```txt
POST /predict/combined
Content-Type: multipart/form-data
```

Form fields:

```txt
text: optional text
file: optional image file
```

At least one of them is required.

Response:

```json
{
  "final_decision": "Rejected",
  "risk_level": "High",
  "reason": "Violence detected in image",
  "recommended_action": "Block content",
  "image_result": {
    "status": "success",
    "prediction": "Violence",
    "confidence": "91.20%",
    "confidence_percentage": 91.2,
    "violence_score": 0.912,
    "safe_score": 0.088,
    "is_violence": true,
    "risk_level": "High",
    "processing_time_ms": 118.5
  },
  "text_result": {
    "original_text": "sample text",
    "is_toxic": false,
    "toxic_confidence_percentage": 8.25,
    "toxic_score": 0.0825,
    "clean_score": 0.9175,
    "risk_level": "Low",
    "highlighted_html_text": "sample text",
    "processing_time_ms": 42.31
  }
}
```
