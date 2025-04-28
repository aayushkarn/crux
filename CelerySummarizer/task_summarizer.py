from transformers import BartTokenizer, BartForConditionalGeneration
import os
import re
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords

# from database.db_engine import SessionLocal
from database.db_models import Summary, Article

"""
ONLY FOR CELERY WORKER
"""

# db = SessionLocal()
nltk.data.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'nltk'))
tokenizer, model = None, None

def load_models():
    global tokenizer, model
    local_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'bart-large-cnn')
    tokenizer = BartTokenizer.from_pretrained(local_model_path)
    model = BartForConditionalGeneration.from_pretrained(local_model_path)
    return tokenizer, model

def chunk_content(content, max_length=1024):
    if len(content)<=max_length:
        return [content]
    
    chunks = []
    current_chunk = ""
    words = content.split(" ")
    for word in words:
        if len(current_chunk) + len(word) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += ' ' + word
            else:
                current_chunk = word
    
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def generate_summary(model, tokenizer, text, max_length=1024):
    inputs = tokenizer(text, return_tensors='pt', max_length=max_length, truncation=True, padding='longest')
    summary_ids = model.generate(inputs['input_ids'], num_beams=4, max_length=100, early_stopping=True)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def refined_summary(model, tokenizer, text):
    inputs = tokenizer(text, return_tensors='pt', max_length=1024, truncation=True)
    summary_ids = model.generate(inputs['input_ids'],num_beams=4, max_length=150)
    refined_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return refined_summary

def summarize_articles(content):
    tokenizer, model = load_models()
    chunks = chunk_content(content)
    summaries = []
    for chunk in chunks:
        summary = generate_summary(model, tokenizer, chunk)
        summaries.append(summary)
    combined_summary = ' '.join(summaries)
    if len(summaries)>1:
        final_summary = generate_summary(model, tokenizer, combined_summary)
        return refined_summary(model, tokenizer, final_summary)
    return refined_summary(model, tokenizer, combined_summary)
    