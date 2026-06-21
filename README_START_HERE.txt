SAFE SPHERE - RUN WITHOUT DOCKER

1) Double click START_BACKEND.bat
2) Wait until it says the API is running on http://127.0.0.1:8000
3) Open http://127.0.0.1:8000/health
4) Double click START_FRONTEND.bat
5) Open http://localhost:5173

Configured paths in backend/.env:
- C:\Users\chann\Downloads\distilbert_sequential_master.pt.zip
- C:\Users\chann\Downloads\master_tokenizer.zip
- C:\Users\chann\Downloads\Copy_of_Violence.ipynb

IMPORTANT:
Copy_of_Violence.ipynb is a notebook, not trained Keras weights.
The backend will not crash because image model loading is optional now,
but the Image Moderation endpoint will stay unavailable until you export
an actual .h5 / .weights.h5 model from that notebook and set VIOLENCE_MODEL_PATH to it.
