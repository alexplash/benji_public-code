
import os
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

HF_TOKEN = os.getenv("HF_TOKEN")

class SentimentAnalyzer:
    
    def __init__(self):
        self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", token = HF_TOKEN)
        self.model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", token = HF_TOKEN)
    
    def classify(self, text):
        inputs = self.tokenizer(text, return_tensors = "pt")
        with torch.no_grad():
            logits = self.model(**inputs).logits
        
        probs = F.softmax(logits, dim = -1)
        return {
            "POSITIVE": float(probs[0][1]),
            "NEGATIVE": float(probs[0][0])
        }