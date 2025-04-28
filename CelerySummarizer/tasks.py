import datetime
from celery import Celery
import redis
from database.db_models import Summary, Article
from . import settings

from database.db_engine import SessionLocal

"""
CELERY TASK THAT NEEDS TO BE PASSED TO BE WORKER
"""

if settings.REMOTE_REDIS:
    app = Celery(
        'tasks', 
        broker=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_IP_ADDRESS}:{settings.REDIS_PORT}/0", 
        backend=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_IP_ADDRESS}:{settings.REDIS_PORT}/0"
    )

    r = redis.Redis(
        host=settings.REDIS_IP_ADDRESS, 
        port=settings.REDIS_PORT, 
        password=settings.REDIS_PASSWORD
    )
else:
    app = Celery(
        'tasks', 
        broker=f"redis://{settings.REDIS_IP_ADDRESS}:{settings.REDIS_PORT}/0", 
        backend=f"redis://{settings.REDIS_IP_ADDRESS}:{settings.REDIS_PORT}/0"
    )

    r = redis.Redis(
        host=settings.REDIS_IP_ADDRESS, 
        port=settings.REDIS_PORT
    )

@app.task
def summarize_cluster(cluster_id):
    from .task_summarizer import summarize_articles
    db = SessionLocal()
    try:
        articles = db.query(Article).filter(Article.cluster_id==cluster_id).all()
        content = ' '.join([a.content for a in articles])
        summary = summarize_articles(content)

        summary_row = db.query(Summary).filter(Summary.cluster_id==cluster_id).first()
        if summary_row:
            summary_row.summary = summary
            db.commit()
            r.delete("summary_api")
            # r.delete(f"summary:{cluster_id}")
            r.srem("summarization_tasks", cluster_id)
            r.delete(f"task_id:{cluster_id}")
    finally:
        db.close()
