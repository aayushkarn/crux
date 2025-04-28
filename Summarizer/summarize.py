from transformers import BartTokenizer, BartForConditionalGeneration
import json
import os
import re
from bs4 import BeautifulSoup
import nltk
from nltk import sent_tokenize
from nltk.corpus import stopwords
from datetime import datetime

from database.db_engine import SessionLocal
from database.db_models import Summary, Article

"""
SUMMARIZER THAT SUMMARIZES ALL REMAINING ARTICLES.
WAS USED INITIALLY BUT NOW MOVED TO CELERY WORKER
"""

db = SessionLocal()
nltk.data.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'nltk'))

def init_summary_db():
    articles = db.query(Article).all()
    # TODO: check later for correctness
    clusters_id = []
    for article in articles:
        if article.cluster_id == None:
            continue
        if article.cluster_id in clusters_id:
            continue
        else:
            clusters_id.append(article.cluster_id)
    # print(len(clusters_id))
    for _id in clusters_id:
        summaries = db.query(Summary).filter(Summary.cluster_id == _id).first()
        if summaries is None:
            summaries = Summary(
                cluster_id = _id
            )
            db.add(summaries)
            db.commit()
    db.close()

def get_all_remaining_articles():
    cluster_ids = db.query(Summary).filter(Summary.summary==None).all()
    pending_articles_list = []
    for cluster in cluster_ids:
        articles = db.query(Article).filter(Article.cluster_id==cluster.cluster_id).all()
        if articles is not None:
            pending_articles_list.append(articles)
    print(f"Pending Summarizations {len(pending_articles_list)}\n")
    return pending_articles_list

def load_models():
    local_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'bart-large-cnn')
    tokenizer = BartTokenizer.from_pretrained(local_model_path)
    model = BartForConditionalGeneration.from_pretrained(local_model_path)
    return tokenizer, model

def filter_article(content, remove_stopword=False):
    # if "<" in content and ">" in content:
    soup = BeautifulSoup(content, "html.parser")
    for script_or_style in soup(['script','style']):
        script_or_style.decompose()
    text = soup.get_text(separator=' ', strip=True)
    cleaned_text = re.sub(r'\n+', ' ', text)  # Replace multiple newlines with a single space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text) 
    filtered_content = re.sub(r'(?i)(source|ads|advertisement|sponsored)', '', cleaned_text)
    if remove_stopword:
        stop_words = set(stopwords.words('english'))
        text_without_stopwords = [word for word in filtered_content.split() if word.lower() not in stop_words]
        return ' '.join(text_without_stopwords)
    return filtered_content

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
    # model.config.forced_bos_token_id = 0
    # generation_config = model.config.to_dict()
    # generation_config['num_beams'] = 4
    # generation_config['max_length'] = 150
    inputs = tokenizer(text, return_tensors='pt', max_length=max_length, truncation=True, padding='longest')
    summary_ids = model.generate(inputs['input_ids'], num_beams=4, max_length=100, early_stopping=True)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def refined_summary(model, tokenizer, text):
    # print(f"SUMMARY: {text}\n")
    inputs = tokenizer(text, return_tensors='pt', max_length=1024, truncation=True)
    summary_ids = model.generate(inputs['input_ids'],num_beams=4, max_length=150)
    refined_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    # print(f"REFINED SUMMARY: {refined_summary}\n")
    return refined_summary

def summarize(content):
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
    


# a = summarize(filter_article(content))


def run_summarizer():
    s1=datetime.now().timestamp()
    print("Running summarizer..")
    init_summary_db()
    pending_sumarrization = get_all_remaining_articles()
    for article in pending_sumarrization:
        content=""
        if len(article)>1:
            for a in article:
                text = a.title + " " + a.content + " "
                content += text
        else:
            text = article[0].title + " " + article[0].content
            content += text
        gen_summary = summarize(content)
        summary_table = db.query(Summary).filter(Summary.cluster_id==article[0].cluster_id).first()
        summary_table.summary = gen_summary
        db.commit()
    e1=datetime.now().timestamp()
    tdelta = e1 - s1
    print(f"\nTime taken {tdelta} seconds")