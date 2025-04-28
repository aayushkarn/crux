import datetime
import uuid
from sentence_transformers import SentenceTransformer
import os
import logging

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering

import config
from database.db_models import Article
from database.db_engine import SessionLocal

db = SessionLocal()

"""
TAKES SCRAPED NEWS ARTICLE WITH CLUSTER_ID NULL FROM DB AND THEN BASED ON THEIR SIMILARITY ASSIGNS A UNIQUE ID FOR ALL SIMILAR NEWS ARTICLES
"""

def load_models():
    local_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'paraphrase-MiniLM-L3-v2')
    model = SentenceTransformer(local_model_path)
    return model

def considerArticleForClustering(article_timestamp,days=config.AVOID_CLUSTER_AFTER_DAYS):
    """
    HELPS CHECK IF THE ARTICLE IS TO BE CONSIDERED FOR CLUSTERING
    """
    article_datetime = datetime.datetime.fromtimestamp(article_timestamp)
    delta = datetime.timedelta(days=days)
    added_days_article = article_datetime + delta
    added_days_article_timestamp = added_days_article.timestamp()
    return added_days_article_timestamp>datetime.datetime.now().timestamp()

def saveClustersToDb(clusters,article_id):
    for i, cluster_id in enumerate(clusters):
        articles = db.query(Article).filter(Article.id==article_id[i]).all()
        for article in articles:
            article.cluster_id = cluster_id
            db.commit()
    db.close()

def cluster():
    articles = db.query(Article).filter(Article.cluster_id==None).all()
    # print(articles)
    print("Clustering..")
    if articles != []:
        if len(articles)<2:
            print("Not enough articles to cluster")
            articles[0].cluster_id = str(uuid.uuid4().hex)
            db.commit()
            db.close()
        else:
            texts = []
            article_id = []
            for article in articles:
                # if considerArticleForClustering(article.publish_timestamp):
                title = article.title
                content = article.content
                full_text = title + " " + content
                texts.append(full_text.lower()) 
                article_id.append(article.id)
            model = load_models()
            embeddings = model.encode(texts, convert_to_numpy=True)
            similarity_matrix = cosine_similarity(embeddings)
            clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=1 - config.CLUSTER_SIMILARITY_THRESHOLD, metric="precomputed", linkage='average')
            clusters = clustering.fit_predict(1-similarity_matrix)
            cluster_uuids = [str(uuid.uuid4().hex) for _ in range(len(set(clusters)))]
            cluster_uuid_map = {cluster_id: cluster_uuid for cluster_id, cluster_uuid in zip(set(clusters), cluster_uuids)}
            uuid_clusters = [cluster_uuid_map[cluster_id] for cluster_id in clusters]
            saveClustersToDb(uuid_clusters, article_id)
    print("Done clustering")