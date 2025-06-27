import torch
from huggingface_hub import hf_hub_download
from transformers import BertTokenizer
from model import MultiTaskBert
import streamlit as st

# Sentiment and aspect mappings
sentiment_map = {0: "Negative", 1: "Positive"}
aspect_map = {
    0: "cleanliness", 1: "cost", 2: "emergency",
    3: "general", 4: "staff", 5: "treatment", 6: "waiting_time"
}

# Caching model loading
@st.cache_resource
def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Download model from Hugging Face Hub
    hf_model_path = "amit2005/sentimed-model"
    model_filename = "multitask_bert_model.pth"
    model_path = hf_hub_download(repo_id=hf_model_path, filename=model_filename)

    # Load tokenizer from pretrained BERT
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    # Load model
    model = MultiTaskBert()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    return model, tokenizer, device

def predict(text):
    model, tokenizer, device = load_model()
    inputs = tokenizer(text, return_tensors='pt', padding='max_length', truncation=True, max_length=128)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    with torch.no_grad():
        s_logits, a_logits = model(input_ids, attention_mask)
    sentiment = torch.argmax(s_logits, dim=1).item()
    aspect = torch.argmax(a_logits, dim=1).item()
    return sentiment, aspect