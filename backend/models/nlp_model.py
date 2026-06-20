import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
import shap

class MasterSequentialModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.transformer = AutoModel.from_pretrained("distilbert-base-uncased")
        self.classifier = nn.Linear(768, 2)
        
    def forward(self, input_ids, attention_mask):
        outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
        cls_token = outputs.last_hidden_state[:, 0, :]
        return self.classifier(cls_token)

def predict_shap_backend(texts, model, tokenizer, device):
    inputs = tokenizer(list(texts), padding='max_length', truncation=True, max_length=128, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(inputs['input_ids'], inputs['attention_mask'])
        probabilities = F.softmax(logits, dim=1)
    return probabilities.cpu().numpy()